"""
data_service.py
Manages downloading and saving DARWIN quotes from the Info API.
"""

import os
import pandas as pd
from .info_api_client import DarwinexInfoAPIClient

class DataService:
    """
    Orchestrates data retrieval and storage for DARWIN quotes.
    """

    def __init__(self, api_client: DarwinexInfoAPIClient):
        """
        :param api_client: An instance of DarwinexInfoAPIClient to fetch data.
        """
        self.api_client = api_client

    def fetch_and_save_quotes(self, product_list, start_date, end_date, save_path="data/raw"):
        """
        For each product in product_list, fetch quotes and save as CSV.
        Catches exceptions to avoid crashing on 404 or similar errors.
        """
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        for product_name in product_list:
            try:
                data = self.api_client.get_quotes(product_name, start_date, end_date)
            except Exception as ex:
                print(f"[ERROR] Could not download data for {product_name}: {ex}")
                continue

            if not data:
                print(f"[WARN] No data returned for {product_name} in {start_date} -> {end_date}. Skipped.")
                continue

            df = self._convert_to_dataframe(data)
            filename = f"{product_name}_{start_date}_{end_date}.csv"
            full_path = os.path.join(save_path, filename)
            df.to_csv(full_path, index=False)
            print(f"[INFO] Saved data to: {full_path}")

    def _convert_to_dataframe(self, raw_data):
        """
        Convert array of [timestamp_ms, quote] into a DataFrame with columns [date, close].
        """
        df = pd.DataFrame(raw_data, columns=["timestamp_ms", "close"])
        df["date"] = pd.to_datetime(df["timestamp_ms"], unit="ms", utc=True)
        df = df[["date", "close"]]
        df.sort_values("date", inplace=True)
        df.reset_index(drop=True, inplace=True)
        return df
