import os
import time
import requests
import pandas as pd
from typing import Dict, List, Any, Tuple
from data_resilience import DataResilienceEngine, clean_str

MONDAY_API_URL = "https://api.monday.com/v2"

class MondayBoardSeeder:
    """
    Automated Monday.com Board Creator & Data Importer.
    Uses Monday.com GraphQL API to create 'Skylark Deals Funnel' and 'Skylark Work Order Tracker'
    boards, configures column structures, and imports rows from cleaned dataset.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.endpoint = MONDAY_API_URL

    def get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "API-Version": "2023-10"
        }

    def execute_graphql(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL query or mutation."""
        res = requests.post(self.endpoint, json={"query": query, "variables": variables or {}}, headers=self.get_headers(), timeout=30)
        if res.status_code == 200:
            return res.json()
        raise Exception(f"GraphQL HTTP Error {res.status_code}: {res.text}")

    def create_board(self, board_name: str, board_kind: str = "public") -> str:
        """Create a new board and return board ID."""
        mutation = """
        mutation ($board_name: String!, $board_kind: BoardKind!) {
          create_board (board_name: $board_name, board_kind: $board_kind) {
            id
          }
        }
        """
        data = self.execute_graphql(mutation, {"board_name": board_name, "board_kind": board_kind})
        board_id = data.get("data", {}).get("create_board", {}).get("id")
        if not board_id:
            raise Exception(f"Failed to create board: {data}")
        return board_id

    def create_column(self, board_id: str, title: str, column_type: str) -> str:
        """Create column on board."""
        mutation = """
        mutation ($board_id: ID!, $title: String!, $column_type: ColumnType!) {
          create_column (board_id: $board_id, title: $title, column_type: $column_type) {
            id
          }
        }
        """
        data = self.execute_graphql(mutation, {"board_id": board_id, "title": title, "column_type": column_type})
        col_id = data.get("data", {}).get("create_column", {}).get("id")
        return col_id

    def create_item(self, board_id: str, item_name: str, column_values: Dict[str, Any]) -> str:
        """Create an item with column values."""
        mutation = """
        mutation ($board_id: ID!, $item_name: String!, $column_values: JSON!) {
          create_item (board_id: $board_id, item_name: $item_name, column_values: $column_values) {
            id
          }
        }
        """
        column_values_json = pd.io.json.dumps(column_values)
        data = self.execute_graphql(mutation, {
            "board_id": board_id,
            "item_name": item_name,
            "column_values": column_values_json
        })
        return data.get("data", {}).get("create_item", {}).get("id", "")

    def seed_deals_board(self, df_deals: pd.DataFrame, max_rows: int = 50) -> str:
        """Create and populate Deals board."""
        print("Creating 'Skylark Deals Funnel' board on Monday.com...")
        board_id = self.create_board("Skylark Deals Funnel")
        print(f"Board created with ID: {board_id}")
        
        # Columns to create
        cols_spec = [
            ("Owner Code", "text"),
            ("Client Code", "text"),
            ("Deal Status", "color"),
            ("Deal Stage", "color"),
            ("Masked Deal Value", "numbers"),
            ("Closure Probability", "text"),
            ("Sector", "text"),
            ("Product Deal", "text"),
            ("Tentative Close Date", "date")
        ]
        
        col_map = {}
        for title, ctype in cols_spec:
            try:
                col_id = self.create_column(board_id, title, ctype)
                col_map[title] = col_id
                time.sleep(0.2)
            except Exception as e:
                print(f"Notice: column '{title}' setup: {e}")
                
        # Populate rows
        print(f"Importing up to {max_rows} deals into Monday.com...")
        count = 0
        for _, row in df_deals.head(max_rows).iterrows():
            item_name = str(row["Deal Name Clean"] or "Unnamed Deal")
            cvals = {}
            if "Owner Code" in col_map:
                cvals[col_map["Owner Code"]] = str(row["Owner Code Clean"])
            if "Client Code" in col_map:
                cvals[col_map["Client Code"]] = str(row["Client Code Clean"])
            if "Masked Deal Value" in col_map:
                cvals[col_map["Masked Deal Value"]] = float(row["Deal Value Clean"])
            if "Sector" in col_map:
                cvals[col_map["Sector"]] = str(row["Sector Clean"])
                
            try:
                self.create_item(board_id, item_name, cvals)
                count += 1
                time.sleep(0.15)
            except Exception as e:
                print(f"Item import notice: {e}")
                
        print(f"Successfully imported {count} deals into Monday board ID {board_id}")
        return board_id

    def seed_work_orders_board(self, df_wo: pd.DataFrame, max_rows: int = 50) -> str:
        """Create and populate Work Orders board."""
        print("Creating 'Skylark Work Order Tracker' board on Monday.com...")
        board_id = self.create_board("Skylark Work Order Tracker")
        print(f"Board created with ID: {board_id}")
        
        cols_spec = [
            ("Customer Name Code", "text"),
            ("Serial #", "text"),
            ("Nature of Work", "text"),
            ("Execution Status", "color"),
            ("BD/KAM Personnel Code", "text"),
            ("Sector", "text"),
            ("Amount Excl GST", "numbers"),
            ("Billed Value", "numbers"),
            ("Collected Amount", "numbers"),
            ("Amount Receivable", "numbers"),
            ("Billing Status", "color")
        ]
        
        col_map = {}
        for title, ctype in cols_spec:
            try:
                col_id = self.create_column(board_id, title, ctype)
                col_map[title] = col_id
                time.sleep(0.2)
            except Exception as e:
                print(f"Notice: column '{title}' setup: {e}")
                
        print(f"Importing up to {max_rows} work orders into Monday.com...")
        count = 0
        for _, row in df_wo.head(max_rows).iterrows():
            item_name = str(row["Deal Name Clean"] or "Unnamed Work Order")
            cvals = {}
            if "Customer Name Code" in col_map:
                cvals[col_map["Customer Name Code"]] = str(row["Customer Code Clean"])
            if "Serial #" in col_map:
                cvals[col_map["Serial #"]] = str(row["Serial Clean"])
            if "Amount Excl GST" in col_map:
                cvals[col_map["Amount Excl GST"]] = float(row["Amount Excl GST Clean"])
            if "Sector" in col_map:
                cvals[col_map["Sector"]] = str(row["Sector Clean"])
                
            try:
                self.create_item(board_id, item_name, cvals)
                count += 1
                time.sleep(0.15)
            except Exception as e:
                print(f"Item import notice: {e}")
                
        print(f"Successfully imported {count} work orders into Monday board ID {board_id}")
        return board_id


if __name__ == "__main__":
    import sys
    api_key = sys.argv[1] if len(sys.argv) > 1 else ""
    if not api_key:
        print("Usage: python monday_seeder.py <MONDAY_API_KEY>")
        sys.exit(1)
        
    deals_path = "/home/gt/Projects/skylark_project/Deal funnel Data.xlsx"
    wo_path = "/home/gt/Projects/skylark_project/Work_Order_Tracker Data.xlsx"
    
    df_deals = DataResilienceEngine.clean_deals_df(pd.read_excel(deals_path))
    df_wo = DataResilienceEngine.clean_work_orders_df(pd.read_excel(wo_path, header=1))
    
    seeder = MondayBoardSeeder(api_key)
    d_id = seeder.seed_deals_board(df_deals, max_rows=20)
    w_id = seeder.seed_work_orders_board(df_wo, max_rows=20)
    print(f"\nSeeding Complete!\nDeals Board ID: {d_id}\nWork Orders Board ID: {w_id}")
