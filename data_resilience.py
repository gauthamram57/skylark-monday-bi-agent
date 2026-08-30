import pandas as pd
import numpy as np
import re
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional

def clean_str(val: Any) -> str:
    """Clean string values, handle NaNs and trailing whitespace."""
    if pd.isna(val) or val is None:
        return ""
    val_str = str(val).strip()
    if val_str.lower() in ["nan", "null", "none", "n/a", "nat"]:
        return ""
    return val_str

def normalize_sector(sector_str: Any) -> str:
    """
    Standardize sector names across Deals and Work Orders.
    Handles case variations, typos, and header leaks.
    """
    s = clean_str(sector_str).lower()
    if not s or s in ["sector/service", "sector", "others", "other"]:
        return "Others / Unspecified"
    
    if "mining" in s:
        return "Mining"
    elif "power" in s or "powerline" in s:
        return "Powerline"
    elif "renew" in s or "solar" in s or "wind" in s:
        return "Renewables"
    elif "rail" in s:
        return "Railways"
    elif "construct" in s or "infra" in s:
        return "Construction"
    elif "secur" in s or "surveil" in s:
        return "Security & Surveillance"
    elif "dsp" in s:
        return "DSP"
    elif "aviation" in s or "airport" in s:
        return "Aviation"
    elif "manufactur" in s:
        return "Manufacturing"
    elif "tender" in s:
        return "Tender"
    else:
        return s.capitalize()

def parse_date(date_val: Any) -> Optional[datetime]:
    """Parse mixed date formats into datetime object."""
    if pd.isna(date_val) or date_val is None:
        return None
    if isinstance(date_val, (pd.Timestamp, datetime)):
        return date_val.to_pydatetime() if isinstance(date_val, pd.Timestamp) else date_val
    
    date_str = str(date_val).strip()
    if not date_str or date_str.lower() in ["nan", "nat", "null", "close date (a)", "date"]:
        return None
    
    # Try standard formats
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%b %Y",
        "%B %Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass
    
    # Fallback with pandas to_datetime
    try:
        dt = pd.to_datetime(date_str, errors='coerce')
        if pd.notna(dt):
            return dt.to_pydatetime()
    except Exception:
        pass
    return None

def get_fiscal_quarter(dt: Optional[datetime]) -> str:
    """
    Get Indian Fiscal Quarter (FY April - March) for a given date.
    Q1: Apr-Jun, Q2: Jul-Sep, Q3: Oct-Dec, Q4: Jan-Mar.
    """
    if dt is None:
        return "Unknown Quarter"
    year = dt.year
    month = dt.month
    if month in [4, 5, 6]:
        return f"Q1 FY{str(year)[-2:]}-{str(year+1)[-2:]}"
    elif month in [7, 8, 9]:
        return f"Q2 FY{str(year)[-2:]}-{str(year+1)[-2:]}"
    elif month in [10, 11, 12]:
        return f"Q3 FY{str(year)[-2:]}-{str(year+1)[-2:]}"
    else:
        return f"Q4 FY{str(year-1)[-2:]}-{str(year)[-2:]}"

def normalize_probability(prob_val: Any, deal_stage: str = "") -> float:
    """
    Normalize closure probability strings/numbers to 0.0 - 1.0 float.
    Handles 'High', 'Medium', 'Low', '80%', stage fallbacks.
    """
    s = clean_str(prob_val).lower()
    if s:
        if s == "high":
            return 0.80
        elif s == "medium":
            return 0.50
        elif s == "low":
            return 0.20
        else:
            # Try parsing numeric percentage or float
            num_str = re.sub(r"[^\d.]", "", s)
            if num_str:
                try:
                    val = float(num_str)
                    if val > 1.0:
                        return min(val / 100.0, 1.0)
                    return max(0.0, val)
                except ValueError:
                    pass
    
    # Fallback to Deal Stage implied probability
    stage = clean_str(deal_stage).upper()
    if any(k in stage for k in ["WORK ORDER RECEIVED", "PROJECT WON", "INVOICE SENT", "AMOUNT ACCRUED", "COMPLETED"]):
        return 1.0
    elif any(k in stage for k in ["LOST", "NOT RELEVANT"]):
        return 0.0
    elif "NEGOTIATIONS" in stage or "PROPOSAL" in stage:
        return 0.60
    elif "FEASIBILITY" in stage or "DEMO" in stage:
        return 0.40
    elif "LEAD GENERATED" in stage or "QUALIFIED" in stage:
        return 0.20
    else:
        return 0.30

def categorize_deal_status(deal_status: str, deal_stage: str) -> str:
    """
    Determine normalized deal status (Won, Lost, Open, On Hold).
    """
    status_str = clean_str(deal_status).lower()
    stage_str = clean_str(deal_stage).lower()
    
    if "won" in status_str or any(k in stage_str for k in ["work order received", "project won", "invoice sent", "amount accrued", "project completed"]):
        return "Won"
    elif "dead" in status_str or "lost" in status_str or any(k in stage_str for k in ["project lost", "not relevant"]):
        return "Lost"
    elif "hold" in status_str or "on hold" in stage_str:
        return "On Hold"
    else:
        return "Open"

class DataResilienceEngine:
    """
    Cleans, normalizes, and audits Deals and Work Orders datasets.
    Provides quality metrics and data resilience warnings for BI queries.
    """

    @staticmethod
    def clean_deals_df(df_raw: pd.DataFrame) -> pd.DataFrame:
        """Clean raw Deals dataframe."""
        df = df_raw.copy()
        
        # Scrub header leaks
        if "Deal Stage" in df.columns:
            df = df[df["Deal Stage"] != "Deal Stage"]
        if "Deal Name" in df.columns:
            df = df[df["Deal Name"] != "Deal Name"]
            
        df = df.dropna(subset=["Deal Name"], how="all").reset_index(drop=True)
        
        # Clean text columns
        df["Deal Name Clean"] = df["Deal Name"].apply(clean_str)
        df["Owner Code Clean"] = df["Owner code"].apply(clean_str)
        df["Client Code Clean"] = df["Client Code"].apply(clean_str)
        df["Product Deal Clean"] = df["Product deal"].apply(clean_str)
        df["Sector Clean"] = df["Sector/service"].apply(normalize_sector)
        df["Deal Stage Clean"] = df["Deal Stage"].apply(clean_str)
        
        # Clean numbers
        df["Deal Value Clean"] = pd.to_numeric(df["Masked Deal value"], errors="coerce").fillna(0.0)
        
        # Probability & Weighted Value
        probabilities = []
        statuses = []
        for _, row in df.iterrows():
            prob = normalize_probability(row.get("Closure Probability"), row.get("Deal Stage Clean", ""))
            status = categorize_deal_status(row.get("Deal Status"), row.get("Deal Stage Clean", ""))
            probabilities.append(prob)
            statuses.append(status)
            
        df["Probability Clean"] = probabilities
        df["Status Clean"] = statuses
        df["Weighted Value"] = df["Deal Value Clean"] * df["Probability Clean"]
        
        # Dates
        df["Created Date Clean"] = df["Created Date"].apply(parse_date)
        df["Tentative Close Date Clean"] = df["Tentative Close Date"].apply(parse_date)
        df["Close Date Clean"] = df["Close Date (A)"].apply(parse_date)
        
        df["Fiscal Quarter"] = df["Tentative Close Date Clean"].apply(get_fiscal_quarter)
        
        return df

    @staticmethod
    def clean_work_orders_df(df_raw: pd.DataFrame) -> pd.DataFrame:
        """Clean raw Work Orders dataframe."""
        df = df_raw.copy()
        
        # Handle blank row 0 if header wasn't set correctly
        if "Deal name masked" not in df.columns and "Unnamed: 0" in df.columns:
            # Check if row 0 has the real header
            if df.iloc[0].astype(str).str.contains("Deal name").any():
                df.columns = df.iloc[0]
                df = df.iloc[1:].reset_index(drop=True)
                
        # Scrub header leaks
        if "Deal name masked" in df.columns:
            df = df[df["Deal name masked"] != "Deal name masked"]
            
        df = df.dropna(subset=["Deal name masked", "Serial #"], how="all").reset_index(drop=True)
        
        # Clean text columns
        df["Deal Name Clean"] = df["Deal name masked"].apply(clean_str)
        df["Customer Code Clean"] = df["Customer Name Code"].apply(clean_str)
        df["Serial Clean"] = df["Serial #"].apply(clean_str)
        df["Nature of Work Clean"] = df["Nature of Work"].apply(clean_str)
        df["Execution Status Clean"] = df["Execution Status"].apply(lambda x: clean_str(x) if clean_str(x) else "Unspecified")
        df["Document Type Clean"] = df["Document Type"].apply(clean_str)
        df["Personnel Code Clean"] = df["BD/KAM Personnel code"].apply(clean_str)
        df["Sector Clean"] = df["Sector"].apply(normalize_sector)
        df["Type of Work Clean"] = df["Type of Work"].apply(clean_str)
        
        # Normalize status fields
        def norm_billing_status(val):
            v = clean_str(val).lower()
            if "partially" in v:
                return "Partially Billed"
            elif "billed" in v:
                return "Billed"
            elif "update" in v:
                return "Update Required"
            else:
                return "Unbilled / Open"
                
        df["Billing Status Clean"] = df.get("Billing Status", pd.Series()).apply(norm_billing_status)
        df["WO Status Clean"] = df["WO Status (billed)"].apply(lambda x: clean_str(x) if clean_str(x) else "Open")
        
        # Clean numeric fields
        num_cols = [
            "Amount in Rupees (Excl of GST) (Masked)",
            "Amount in Rupees (Incl of GST) (Masked)",
            "Billed Value in Rupees (Excl of GST.) (Masked)",
            "Billed Value in Rupees (Incl of GST.) (Masked)",
            "Collected Amount in Rupees (Incl of GST.) (Masked)",
            "Amount to be billed in Rs. (Exl. of GST) (Masked)",
            "Amount to be billed in Rs. (Incl. of GST) (Masked)",
            "Amount Receivable (Masked)"
        ]
        for col in num_cols:
            clean_col_name = col.replace(" (Masked)", "").replace(" in Rupees", "").replace(" in Rs.", "").strip()
            df[col + " Clean"] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0.0)
            
        # Standard field aliases
        df["Amount Excl GST Clean"] = df["Amount in Rupees (Excl of GST) (Masked) Clean"]
        df["Amount Incl GST Clean"] = df["Amount in Rupees (Incl of GST) (Masked) Clean"]
        df["Billed Excl GST Clean"] = df["Billed Value in Rupees (Excl of GST.) (Masked) Clean"]
        df["Collected Incl GST Clean"] = df["Collected Amount in Rupees (Incl of GST.) (Masked) Clean"]
        df["Unbilled Excl GST Clean"] = df["Amount to be billed in Rs. (Exl. of GST) (Masked) Clean"]
        df["Receivable Clean"] = df["Amount Receivable (Masked) Clean"]
        
        # Clean Dates
        df["PO Date Clean"] = df["Date of PO/LOI"].apply(parse_date)
        df["Start Date Clean"] = df["Probable Start Date"].apply(parse_date)
        df["End Date Clean"] = df["Probable End Date"].apply(parse_date)
        df["Delivery Date Clean"] = df["Data Delivery Date"].apply(parse_date)
        df["Invoice Date Clean"] = df["Last invoice date"].apply(parse_date)
        
        df["Fiscal Quarter"] = df["PO Date Clean"].apply(get_fiscal_quarter)
        
        return df

    @staticmethod
    def audit_dataset_quality(df_deals: pd.DataFrame, df_wo: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive data completeness & quality report."""
        deals_total = len(df_deals)
        deals_missing_val = (df_deals["Deal Value Clean"] == 0).sum()
        deals_missing_prob = (df_deals["Closure Probability"].isna()).sum()
        deals_missing_sector = (df_deals["Sector Clean"] == "Others / Unspecified").sum()
        
        wo_total = len(df_wo)
        wo_missing_billed = (df_wo["Billed Excl GST Clean"] == 0).sum()
        wo_missing_collected = (df_wo["Collected Incl GST Clean"] == 0).sum()
        wo_unbilled_backlog = (df_wo["Unbilled Excl GST Clean"] > 0).sum()
        
        deals_score = max(0, 100 - int((deals_missing_val * 0.4 + deals_missing_prob * 0.3 + deals_missing_sector * 0.3) / max(deals_total, 1) * 100))
        wo_score = max(0, 100 - int((wo_missing_billed * 0.5 + wo_missing_collected * 0.5) / max(wo_total, 1) * 100))
        
        warnings = []
        if deals_missing_val > 0:
            warnings.append(f"⚠️ {deals_missing_val} out of {deals_total} deals have missing/zero deal values.")
        if deals_missing_prob > 0:
            warnings.append(f"ℹ️ {deals_missing_prob} deals missing explicit closure probability; stage-based heuristic applied.")
        if wo_unbilled_backlog > 0:
            warnings.append(f"📊 {wo_unbilled_backlog} out of {wo_total} work orders have pending unbilled contract amounts.")
            
        return {
            "deals_total": deals_total,
            "deals_quality_score": deals_score,
            "deals_missing_value_count": deals_missing_val,
            "deals_missing_prob_count": deals_missing_prob,
            "wo_total": wo_total,
            "wo_quality_score": wo_score,
            "overall_quality_score": (deals_score + wo_score) // 2,
            "warnings": warnings
        }
