import os
import json
import requests
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from data_resilience import DataResilienceEngine, clean_str, normalize_sector

MONDAY_API_URL = "https://api.monday.com/v2"

class MondayGraphQLClient:
    """
    Monday.com API v2 GraphQL Client.
    Handles authentication, dynamic GraphQL queries, and error handling.
    """
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or os.getenv("MONDAY_API_KEY", "")
        self.endpoint = MONDAY_API_URL

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "API-Version": "2023-10"
        }

    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection and token validity."""
        if not self.api_key:
            return False, "No Monday.com API Key provided."
        
        query = "{ me { id name email } }"
        try:
            res = requests.post(self.endpoint, json={"query": query}, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                data = res.json()
                if "errors" in data:
                    return False, f"GraphQL Error: {data['errors'][0].get('message')}"
                me = data.get("data", {}).get("me", {})
                return True, f"Connected successfully as {me.get('name')} ({me.get('email')})"
            return False, f"HTTP Error {res.status_code}: {res.text}"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def fetch_board_items(self, board_id: str) -> List[Dict[str, Any]]:
        """Fetch all items and column values from a Monday.com board."""
        if not self.api_key or not board_id:
            return []
        
        query = """
        query ($board_id: [ID!]) {
          boards(ids: $board_id) {
            id
            name
            columns {
              id
              title
              type
            }
            items_page(limit: 500) {
              items {
                id
                name
                created_at
                column_values {
                  id
                  text
                  value
                }
              }
            }
          }
        }
        """
        variables = {"board_id": [str(board_id)]}
        try:
            res = requests.post(self.endpoint, json={"query": query, "variables": variables}, headers=self.get_headers(), timeout=15)
            if res.status_code == 200:
                data = res.json()
                boards = data.get("data", {}).get("boards", [])
                if boards:
                    items = boards[0].get("items_page", {}).get("items", [])
                    return items
        except Exception as e:
            print(f"Error fetching Monday board {board_id}: {e}")
        return []

    def fetch_all_boards(self) -> List[Dict[str, Any]]:
        """List all accessible boards."""
        if not self.api_key:
            return []
        query = "{ boards(limit: 50) { id name board_folder_id state } }"
        try:
            res = requests.post(self.endpoint, json={"query": query}, headers=self.get_headers(), timeout=10)
            if res.status_code == 200:
                return res.json().get("data", {}).get("boards", [])
        except Exception:
            pass
        return []


class MondayMockEngine:
    """
    Dynamic Monday.com Board Simulator & Dynamic Data Provider.
    If no API key is provided, this engine loads raw datasets, applies Data Resilience,
    and returns Monday.com compliant board schema structures dynamically.
    """
    def __init__(self, deals_path: str, wo_path: str):
        self.deals_path = deals_path
        self.wo_path = wo_path
        
        # Raw Dataframes
        self.df_deals_raw = pd.read_excel(deals_path)
        self.df_wo_raw = pd.read_excel(wo_path, header=1)
        
        # Cleaned Dataframes via Data Resilience Engine
        self.df_deals = DataResilienceEngine.clean_deals_df(self.df_deals_raw)
        self.df_wo = DataResilienceEngine.clean_work_orders_df(self.df_wo_raw)
        
        # Audit Quality Report
        self.quality_report = DataResilienceEngine.audit_dataset_quality(self.df_deals, self.df_wo)

    def get_deals_board_items(self) -> List[Dict[str, Any]]:
        """Format clean Deals dataframe as Monday.com GraphQL item objects."""
        items = []
        for idx, row in self.df_deals.iterrows():
            item_id = str(1000 + idx)
            cols = [
                {"id": "text_owner", "title": "Owner Code", "text": str(row["Owner Code Clean"])},
                {"id": "text_client", "title": "Client Code", "text": str(row["Client Code Clean"])},
                {"id": "status_deal_status", "title": "Deal Status", "text": str(row["Status Clean"])},
                {"id": "status_stage", "title": "Deal Stage", "text": str(row["Deal Stage Clean"])},
                {"id": "numeric_deal_value", "title": "Masked Deal Value", "text": str(row["Deal Value Clean"])},
                {"id": "text_probability", "title": "Closure Probability", "text": f"{int(row['Probability Clean']*100)}%"},
                {"id": "numeric_weighted_val", "title": "Weighted Value", "text": str(row["Weighted Value"])},
                {"id": "text_sector", "title": "Sector/Service", "text": str(row["Sector Clean"])},
                {"id": "text_product", "title": "Product Deal", "text": str(row["Product Deal Clean"])},
                {"id": "date_tentative", "title": "Tentative Close Date", "text": str(row["Tentative Close Date Clean"] or "")},
                {"id": "date_created", "title": "Created Date", "text": str(row["Created Date Clean"] or "")},
                {"id": "text_quarter", "title": "Fiscal Quarter", "text": str(row["Fiscal Quarter"])}
            ]
            items.append({
                "id": item_id,
                "name": str(row["Deal Name Clean"] or f"Deal #{item_id}"),
                "column_values": cols,
                "raw_row": row.to_dict()
            })
        return items

    def get_wo_board_items(self) -> List[Dict[str, Any]]:
        """Format clean Work Orders dataframe as Monday.com GraphQL item objects."""
        items = []
        for idx, row in self.df_wo.iterrows():
            item_id = str(5000 + idx)
            cols = [
                {"id": "text_customer", "title": "Customer Name Code", "text": str(row["Customer Code Clean"])},
                {"id": "text_serial", "title": "Serial #", "text": str(row["Serial Clean"])},
                {"id": "text_nature", "title": "Nature of Work", "text": str(row["Nature of Work Clean"])},
                {"id": "status_execution", "title": "Execution Status", "text": str(row["Execution Status Clean"])},
                {"id": "text_personnel", "title": "BD/KAM Personnel Code", "text": str(row["Personnel Code Clean"])},
                {"id": "text_sector", "title": "Sector", "text": str(row["Sector Clean"])},
                {"id": "text_work_type", "title": "Type of Work", "text": str(row["Type of Work Clean"])},
                {"id": "numeric_amount_excl", "title": "Amount (Excl GST)", "text": str(row["Amount Excl GST Clean"])},
                {"id": "numeric_amount_incl", "title": "Amount (Incl GST)", "text": str(row["Amount Incl GST Clean"])},
                {"id": "numeric_billed", "title": "Billed Value", "text": str(row["Billed Excl GST Clean"])},
                {"id": "numeric_collected", "title": "Collected Amount", "text": str(row["Collected Incl GST Clean"])},
                {"id": "numeric_unbilled", "title": "Amount to be Billed", "text": str(row["Unbilled Excl GST Clean"])},
                {"id": "numeric_receivable", "title": "Amount Receivable", "text": str(row["Receivable Clean"])},
                {"id": "status_billing", "title": "Billing Status", "text": str(row["Billing Status Clean"])},
                {"id": "status_wo", "title": "WO Status (Billed)", "text": str(row["WO Status Clean"])},
                {"id": "date_po", "title": "Date of PO/LOI", "text": str(row["PO Date Clean"] or "")},
                {"id": "text_quarter", "title": "Fiscal Quarter", "text": str(row["Fiscal Quarter"])}
            ]
            items.append({
                "id": item_id,
                "name": str(row["Deal Name Clean"] or f"WO #{item_id}"),
                "column_values": cols,
                "raw_row": row.to_dict()
            })
        return items


class MondayDataManager:
    """
    Unified Data Manager. Interacts with either Real Monday.com API or Mock Engine.
    Exposes uniform Pandas DataFrames and Item structures to the BI Agent.
    """
    def __init__(self, deals_excel_path: str, wo_excel_path: str, api_key: str = "", deals_board_id: str = "", wo_board_id: str = ""):
        self.deals_excel_path = deals_excel_path
        self.wo_excel_path = wo_excel_path
        self.api_key = api_key
        self.deals_board_id = deals_board_id
        self.wo_board_id = wo_board_id
        
        self.client = MondayGraphQLClient(api_key)
        self.mock_engine = MondayMockEngine(deals_excel_path, wo_excel_path)
        
        # Load active data
        self.refresh_data()

    def refresh_data(self):
        """Fetch latest data from live Monday API if configured, else from mock engine."""
        self.is_live = False
        self.connection_status = "Using Offline / Simulated Monday.com Data Provider"
        
        if self.api_key and self.deals_board_id:
            ok, msg = self.client.test_connection()
            if ok:
                items_deals = self.client.fetch_board_items(self.deals_board_id)
                items_wo = self.client.fetch_board_items(self.wo_board_id) if self.wo_board_id else []
                if items_deals:
                    self.is_live = True
                    self.connection_status = f"Connected Live to Monday.com (Deals Board ID: {self.deals_board_id})"
                    # Process live items into DataFrames
                    self.df_deals = self._monday_items_to_deals_df(items_deals)
                    self.df_wo = self._monday_items_to_wo_df(items_wo) if items_wo else self.mock_engine.df_wo
                    self.quality_report = DataResilienceEngine.audit_dataset_quality(self.df_deals, self.df_wo)
                    return
        
        # Fallback to Mock Engine
        self.df_deals = self.mock_engine.df_deals
        self.df_wo = self.mock_engine.df_wo
        self.quality_report = self.mock_engine.quality_report

    def _monday_items_to_deals_df(self, items: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert GraphQL items array from real Monday API to cleaned Deals DataFrame."""
        rows = []
        for item in items:
            row = {"Deal Name": item.get("name", "")}
            for cv in item.get("column_values", []):
                title = cv.get("id", "")
                text = cv.get("text", "")
                row[title] = text
            rows.append(row)
        df_raw = pd.DataFrame(rows)
        return DataResilienceEngine.clean_deals_df(df_raw)

    def _monday_items_to_wo_df(self, items: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert GraphQL items array from real Monday API to cleaned Work Orders DataFrame."""
        rows = []
        for item in items:
            row = {"Deal name masked": item.get("name", "")}
            for cv in item.get("column_values", []):
                title = cv.get("id", "")
                text = cv.get("text", "")
                row[title] = text
            rows.append(row)
        df_raw = pd.DataFrame(rows)
        return DataResilienceEngine.clean_work_orders_df(df_raw)
