"""
info_api_client.py
Handles Darwinex Info API requests with Bearer token from .env
"""

import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()

class DarwinexInfoAPIClient:
    """
    Class to manage authentication and requests to the Darwinex Info API (v2.1).

    Attributes:
        api_key (str): Darwinex Info API key.
        base_url (str): The base URL for the Info API.
    """

    def __init__(self, api_key=None):
        """
        Initialize the client, loading the API key from .env if none is provided.

        :param api_key: Darwinex Info API key string or None.
        """
        self.api_key = api_key or os.getenv("DARWINEX_API_KEY")
        self.base_url = "https://api.darwinex.com/darwininfo/2.1"

    def _date_to_epoch_ms(self, date_str: str) -> int:
        """
        Convert YYYY-MM-DD to epoch milliseconds.

        :param date_str: Date string like "2022-01-01"
        :return: Integer epoch in milliseconds
        """
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)

    def get_quotes(self, product_name: str, start_date: str, end_date: str):
        """
        Retrieve historical quotes from /products/{productName}/history/quotes

        :param product_name: DARWIN symbol like "PXQ"
        :param start_date: Start date in "YYYY-MM-DD"
        :param end_date: End date in "YYYY-MM-DD"
        :return: A list of [timestamp_ms, quote] items
        """
        start_ms = self._date_to_epoch_ms(start_date)
        end_ms = self._date_to_epoch_ms(end_date)

        url = f"{self.base_url}/products/{product_name}/history/quotes"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        params = {"start": start_ms, "end": end_ms}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
