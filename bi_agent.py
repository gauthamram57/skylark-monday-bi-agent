import pandas as pd
import numpy as np
import re
from typing import Dict, List, Any, Optional, Tuple
from data_resilience import DataResilienceEngine, clean_str, normalize_sector
from monday_client import MondayDataManager

class BusinessIntelligenceAgent:
    """
    Founder-Level Business Intelligence Agent for Monday.com.
    Interprets natural language queries, queries Deals & Work Orders boards,
    runs cross-board synthesis, generates strategic executive insights,
    handles data quality caveats, and asks clarifying questions when needed.
    """
    def __init__(self, data_manager: MondayDataManager):
        self.dm = data_manager

    def parse_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify intent, sector filters, timeframe, and target boards from natural language.
        """
        q = query.lower().strip()
        
        # 1. Sector Identification
        sectors = []
        if "energy" in q or "power" in q or "powerline" in q:
            sectors.append("Powerline")
        if "mining" in q:
            sectors.append("Mining")
        if "renewable" in q or "solar" in q or "wind" in q:
            sectors.append("Renewables")
        if "rail" in q:
            sectors.append("Railways")
        if "construct" in q or "infra" in q:
            sectors.append("Construction")
        if "secur" in q or "surveil" in q:
            sectors.append("Security & Surveillance")
            
        # 2. Timeframe Identification
        quarter = None
        if "q1" in q:
            quarter = "Q1"
        elif "q2" in q:
            quarter = "Q2"
        elif "q3" in q:
            quarter = "Q3"
        elif "q4" in q:
            quarter = "Q4"
        elif "this quarter" in q or "current quarter" in q:
            quarter = "Q3 FY25-26" # Standard active evaluation quarter
            
        # 3. Intent & Topic Classification
        intent = "general_summary"
        if any(k in q for k in ["pipeline", "funnel", "lead", "deal", "closure", "won", "lost"]):
            intent = "pipeline_health"
        elif any(k in q for k in ["revenue", "billed", "invoice", "collected", "receivable", "ar", "collection"]):
            intent = "financial_performance"
        elif any(k in q for k in ["work order", "execution", "completion", "operational", "delay", "status", "delivery"]):
            intent = "operational_metrics"
        elif any(k in q for k in ["sector", "compare", "breakdown", "performance", "top sector"]):
            intent = "sector_performance"
        elif any(k in q for k in ["leadership", "update", "briefing", "summary", "board update"]):
            intent = "leadership_update"
            
        # 4. Check for ambiguity
        needs_clarification = False
        clarification_msg = ""
        if len(q.split()) < 3 and intent == "general_summary":
            needs_clarification = True
            clarification_msg = "Could you please specify which area you'd like insights on? For example: Pipeline Health, Revenue & Collections, Sectoral Breakdown, or Operational Execution?"

        return {
            "query": query,
            "intent": intent,
            "sectors": sectors,
            "quarter": quarter,
            "needs_clarification": needs_clarification,
            "clarification_msg": clarification_msg
        }

    def answer_query(self, query: str) -> Dict[str, Any]:
        """
        Process query end-to-end and generate comprehensive executive response.
        """
        parsed = self.parse_query_intent(query)
        if parsed["needs_clarification"]:
            return {
                "query": query,
                "status": "clarification_needed",
                "response_text": parsed["clarification_msg"],
                "options": [
                    "How's our pipeline looking for energy sector this quarter?",
                    "What is our total revenue, billed value, and uncollected AR?",
                    "Show operational execution status of work orders by sector",
                    "Prepare an executive summary for leadership update"
                ],
                "data_warnings": self.dm.quality_report["warnings"]
            }
            
        intent = parsed["intent"]
        df_deals = self.dm.df_deals
        df_wo = self.dm.df_wo
        
        # Apply Sector Filters if specified
        if parsed["sectors"]:
            df_deals = df_deals[df_deals["Sector Clean"].isin(parsed["sectors"])]
            df_wo = df_wo[df_wo["Sector Clean"].isin(parsed["sectors"])]
            
        # Route to intent handler
        if intent == "pipeline_health":
            return self._analyze_pipeline_health(query, df_deals, parsed)
        elif intent == "financial_performance":
            return self._analyze_financial_performance(query, df_wo, parsed)
        elif intent == "operational_metrics":
            return self._analyze_operational_metrics(query, df_wo, parsed)
        elif intent == "sector_performance":
            return self._analyze_sector_performance(query, df_deals, df_wo, parsed)
        else:
            return self._analyze_cross_board_overview(query, df_deals, df_wo, parsed)

    def _analyze_pipeline_health(self, query: str, df: pd.DataFrame, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sales pipeline, weighted value, win rates, and stage distribution."""
        total_deals = len(df)
        total_val = df["Deal Value Clean"].sum()
        weighted_val = df["Weighted Value"].sum()
        
        won_df = df[df["Status Clean"] == "Won"]
        lost_df = df[df["Status Clean"] == "Lost"]
        open_df = df[df["Status Clean"] == "Open"]
        hold_df = df[df["Status Clean"] == "On Hold"]
        
        win_count = len(won_df)
        lost_count = len(lost_df)
        open_count = len(open_df)
        closed_total = win_count + lost_count
        win_rate = (win_count / closed_total * 100) if closed_total > 0 else 0.0
        
        open_val = open_df['Deal Value Clean'].sum()
        open_weighted = open_df['Weighted Value'].sum()
        won_val = won_df['Deal Value Clean'].sum()
        lost_val = lost_df['Deal Value Clean'].sum()
        
        headline = f"### Pipeline Overview for {sec_str}\n"
        headline += f"- **Active Open Pipeline**: {open_count} open deals worth **₹{open_val:,.2f}** (Weighted Probability Value: **₹{open_weighted:,.2f}**)\n"
        headline += f"- **Closed Won Deals**: {win_count} won deals worth **₹{won_val:,.2f}**\n"
        headline += f"- **Historical Win Rate**: **{win_rate:.1f}%** ({win_count} Won / {closed_total} Closed)\n"
        headline += f"- **Total Recorded Funnel**: {total_deals} total deals (Gross Value: ₹{total_val:,.2f}, Total Weighted Value: ₹{weighted_val:,.2f})\n"
        if lost_val > 100000000:
            headline += f"- *Data Resilience Note*: Includes {lost_count} lost deals worth ₹{lost_val:,.2f} (e.g. lost tender/enterprise deal Giorno).\n"
        
        # Breakdown by Deal Stage
        stage_summary = df.groupby("Deal Stage Clean").agg(
            Deal_Count=("Deal Name Clean", "count"),
            Gross_Value=("Deal Value Clean", "sum"),
            Weighted_Value=("Weighted Value", "sum")
        ).reset_index().sort_values(by="Gross_Value", ascending=False)
        
        insights = [
            f"Active Open Opportunity: Currently {open_count} active open deals in negotiation/proposal stage with probability-adjusted weighted value of ₹{open_weighted:,.2f}.",
            f"Win Rate Performance: {sec_str} sector exhibits a {win_rate:.1f}% closure rate across historical deals.",
            f"Data Coverage: {(df['Deal Value Clean'] == 0).sum()} deals in this dataset have unpriced zero-value placeholders."
        ]
        
        # Recommendations
        recommendations = [
            "Prioritize top proposal/commercial stage deals to accelerate close dates before quarter end.",
            "Conduct deal scrub on unpriced open leads to establish clear quota targets."
        ]
        
        return {
            "query": query,
            "status": "success",
            "headline": headline,
            "response_text": headline,
            "table_data": stage_summary.to_dict(orient="records"),
            "insights": insights,
            "recommendations": recommendations,
            "chart_type": "bar",
            "chart_data": {
                "x": stage_summary["Deal Stage Clean"].tolist(),
                "y": stage_summary["Gross_Value"].tolist(),
                "title": f"Gross Deal Value by Funnel Stage ({sec_str})"
            },
            "data_warnings": self.dm.quality_report["warnings"]
        }

    def _analyze_financial_performance(self, query: str, df_wo: pd.DataFrame, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze revenue, billed value, collection efficiency, and AR receivables."""
        total_wo = len(df_wo)
        total_contract = df_wo["Amount Excl GST Clean"].sum()
        total_billed = df_wo["Billed Excl GST Clean"].sum()
        total_collected = df_wo["Collected Incl GST Clean"].sum()
        total_unbilled = df_wo["Unbilled Excl GST Clean"].sum()
        total_receivable = df_wo["Receivable Clean"].sum()
        
        collection_efficiency = (total_collected / total_billed * 100) if total_billed > 0 else 0.0
        
        sec_str = ", ".join(parsed["sectors"]) if parsed["sectors"] else "All Sectors"
        
        headline = f"### 💰 Financial & Revenue Performance ({sec_str})\n"
        headline += f"- **Total Contracted Order Value (Excl GST)**: ₹{total_contract:,.2f}\n"
        headline += f"- **Total Billed Value (Excl GST)**: ₹{total_billed:,.2f} ({total_billed/max(total_contract,1)*100:.1f}% Billed)\n"
        headline += f"- **Total Collected Amount (Incl GST)**: ₹{total_collected:,.2f}\n"
        headline += f"- **Unbilled Backlog**: ₹{total_unbilled:,.2f}\n"
        headline += f"- **Outstanding Accounts Receivable (AR)**: ₹{total_receivable:,.2f}\n"
        
        # Financial breakdown by billing status
        billing_summary = df_wo.groupby("Billing Status Clean").agg(
            WO_Count=("Serial Clean", "count"),
            Contract_Value=("Amount Excl GST Clean", "sum"),
            Billed_Value=("Billed Excl GST Clean", "sum"),
            Receivable=("Receivable Clean", "sum")
        ).reset_index()
        
        insights = [
            f"💵 **Collection Realization**: Realized ₹{total_collected:,.2f} in actual collections.",
            f"📌 **Unbilled Backlog Risk**: ₹{total_unbilled:,.2f} worth of executed/ongoing contracts are pending invoice generation.",
            f"🚨 **Receivables Concentration**: Outstanding receivables stand at ₹{total_receivable:,.2f} across { (df_wo['Receivable Clean'] > 0).sum() } work orders."
        ]
        
        recommendations = [
            "Accelerate billing milestones for completed work orders to convert unbilled backlog into active receivables.",
            "Establish dedicated AR follow-up calls for accounts with outstanding receivables."
        ]
        
        return {
            "query": query,
            "status": "success",
            "headline": headline,
            "response_text": headline,
            "table_data": billing_summary.to_dict(orient="records"),
            "insights": insights,
            "recommendations": recommendations,
            "chart_type": "pie",
            "chart_data": {
                "labels": billing_summary["Billing Status Clean"].tolist(),
                "values": billing_summary["Contract_Value"].tolist(),
                "title": f"Contract Value Distribution by Billing Status ({sec_str})"
            },
            "data_warnings": self.dm.quality_report["warnings"]
        }

    def _analyze_operational_metrics(self, query: str, df_wo: pd.DataFrame, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze project execution status, delivery timelines, delay risks, and nature of work."""
        total_wo = len(df_wo)
        exec_counts = df_wo["Execution Status Clean"].value_counts().to_dict()
        
        completed_count = exec_counts.get("Completed", 0)
        ongoing_count = exec_counts.get("Ongoing", 0)
        executed_curr = exec_counts.get("Executed until current month", 0)
        not_started = exec_counts.get("Not Started", 0)
        paused_count = exec_counts.get("Pause / struck", 0)
        
        sec_str = ", ".join(parsed["sectors"]) if parsed["sectors"] else "All Sectors"
        
        headline = f"### 🛠️ Operational Work Order Execution ({sec_str})\n"
        headline += f"- **Total Active Work Orders**: {total_wo}\n"
        headline += f"- **Completed Projects**: {completed_count} ({completed_count/max(total_wo,1)*100:.1f}%)\n"
        headline += f"- **Ongoing Execution**: {ongoing_count} ({ongoing_count/max(total_wo,1)*100:.1f}%)\n"
        headline += f"- **Recurring Contracts Executed Current Month**: {executed_curr}\n"
        headline += f"- **Paused / Struck Orders**: {paused_count}\n"
        headline += f"- **Not Started**: {not_started}\n"
        
        exec_summary = df_wo.groupby("Execution Status Clean").agg(
            Work_Orders=("Serial Clean", "count"),
            Total_Value=("Amount Excl GST Clean", "sum")
        ).reset_index().sort_values(by="Work_Orders", ascending=False)
        
        insights = [
            f"✅ **Completion Efficiency**: {completed_count} projects successfully completed execution.",
            f"⚠️ **Execution Bottleneck**: {paused_count} projects are currently paused or stuck awaiting client inputs."
        ]
        
        recommendations = [
            "Assign dedicated ops leads to resolve client blocker dependencies on paused work orders.",
            "Ensure data delivery dates are logged for all completed projects to streamline invoice generation."
        ]
        
        return {
            "query": query,
            "status": "success",
            "headline": headline,
            "response_text": headline,
            "table_data": exec_summary.to_dict(orient="records"),
            "insights": insights,
            "recommendations": recommendations,
            "chart_type": "bar",
            "chart_data": {
                "x": exec_summary["Execution Status Clean"].tolist(),
                "y": exec_summary["Work_Orders"].tolist(),
                "title": f"Work Orders by Execution Status ({sec_str})"
            },
            "data_warnings": self.dm.quality_report["warnings"]
        }

    def _analyze_sector_performance(self, query: str, df_deals: pd.DataFrame, df_wo: pd.DataFrame, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Cross-sector analysis comparing pipeline vs revenue execution."""
        deals_sector = df_deals.groupby("Sector Clean").agg(
            Deals_Count=("Deal Name Clean", "count"),
            Gross_Pipeline=("Deal Value Clean", "sum"),
            Weighted_Pipeline=("Weighted Value", "sum")
        ).reset_index()
        
        wo_sector = df_wo.groupby("Sector Clean").agg(
            WO_Count=("Serial Clean", "count"),
            Contract_Value=("Amount Excl GST Clean", "sum"),
            Billed_Value=("Billed Excl GST Clean", "sum"),
            Collected_Value=("Collected Incl GST Clean", "sum")
        ).reset_index()
        
        merged = pd.merge(deals_sector, wo_sector, on="Sector Clean", how="outer").fillna(0)
        merged = merged.sort_values(by="Gross_Pipeline", ascending=False)
        
        headline = "### 🌐 Sectoral Performance & Cross-Board Comparison\n"
        headline += f"- Analyzed performance across {len(merged)} distinct sectors.\n"
        top_sec = merged.iloc[0]["Sector Clean"] if len(merged) > 0 else "N/A"
        headline += f"- **Dominant Sector by Pipeline**: {top_sec} (₹{merged.iloc[0]['Gross_Pipeline']:,.2f})\n"
        
        insights = [
            f"🏆 **Top Sector Leader**: {top_sec} leads sales volume across deals funnel.",
            "🔄 **Cross-Board Alignment**: High-volume sales sectors require matched operational capacity to maintain execution SLAs."
        ]
        
        recommendations = [
            "Reallocate sales engineering capacity toward top-performing sectors.",
            "Monitor sector-specific contract-to-billing conversion ratios."
        ]
        
        return {
            "query": query,
            "status": "success",
            "headline": headline,
            "response_text": headline,
            "table_data": merged.to_dict(orient="records"),
            "insights": insights,
            "recommendations": recommendations,
            "chart_type": "bar",
            "chart_data": {
                "x": merged["Sector Clean"].tolist(),
                "y": merged["Gross_Pipeline"].tolist(),
                "title": "Gross Sales Pipeline by Sector"
            },
            "data_warnings": self.dm.quality_report["warnings"]
        }

    def _analyze_cross_board_overview(self, query: str, df_deals: pd.DataFrame, df_wo: pd.DataFrame, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive executive summary crossing Deals funnel and Work Order execution."""
        total_pipeline = df_deals["Deal Value Clean"].sum()
        weighted_pipeline = df_deals["Weighted Value"].sum()
        total_contracted = df_wo["Amount Excl GST Clean"].sum()
        total_billed = df_wo["Billed Excl GST Clean"].sum()
        total_collected = df_wo["Collected Incl GST Clean"].sum()
        
        headline = "### 🏢 Skylark Drones Executive Business Overview\n"
        headline += f"- **Gross Sales Funnel (Deals)**: ₹{total_pipeline:,.2f} ({len(df_deals)} deals)\n"
        headline += f"- **Weighted Funnel Value**: ₹{weighted_pipeline:,.2f}\n"
        headline += f"- **Contracted Work Orders Value**: ₹{total_contracted:,.2f} ({len(df_wo)} work orders)\n"
        headline += f"- **Billed Revenue Value**: ₹{total_billed:,.2f}\n"
        headline += f"- **Cash Collected (Incl GST)**: ₹{total_collected:,.2f}\n"
        
        insights = [
            f"📈 **Funnel Health**: Active pipeline stands at ₹{total_pipeline:,.2f} with weighted probability-adjusted value of ₹{weighted_pipeline:,.2f}.",
            f"⚙️ **Operations Realization**: Work Order contract backlog is ₹{total_contracted:,.2f}, with ₹{total_billed:,.2f} already billed.",
            f"🛡️ **Data Resilience Score**: Overall Dataset Integrity Score is {self.dm.quality_report['overall_quality_score']}/100."
        ]
        
        recommendations = [
            "Conduct weekly sync between Sales and Operations to align won deal handoffs with work order generation.",
            "Focus collection efforts on top outstanding AR accounts to maximize cash flow."
        ]
        
        overview_summary = [
            {"Metric": "Gross Sales Pipeline", "Value (INR)": f"₹{total_pipeline:,.2f}", "Count": len(df_deals)},
            {"Metric": "Weighted Sales Pipeline", "Value (INR)": f"₹{weighted_pipeline:,.2f}", "Count": len(df_deals)},
            {"Metric": "Contracted Work Orders", "Value (INR)": f"₹{total_contracted:,.2f}", "Count": len(df_wo)},
            {"Metric": "Billed Value", "Value (INR)": f"₹{total_billed:,.2f}", "Count": (df_wo['Billed Excl GST Clean'] > 0).sum()},
            {"Metric": "Cash Collected", "Value (INR)": f"₹{total_collected:,.2f}", "Count": (df_wo['Collected Incl GST Clean'] > 0).sum()}
        ]
        
        return {
            "query": query,
            "status": "success",
            "headline": headline,
            "response_text": headline,
            "table_data": overview_summary,
            "insights": insights,
            "recommendations": recommendations,
            "chart_type": "bar",
            "chart_data": {
                "x": [item["Metric"] for item in overview_summary],
                "y": [float(re.sub(r"[^\d.]", "", item["Value (INR)"])) for item in overview_summary],
                "title": "Skylark Drones Executive Key Metrics (INR)"
            },
            "data_warnings": self.dm.quality_report["warnings"]
        }
