"""
test_data_fetcher.py
Tests for data fetching. We mock requests to avoid calling Darwinex API.
"""

import pytest
from unittest.mock import patch
from src.data_fetcher.info_api_client import DarwinexInfoAPIClient
from src.data_fetcher.data_service import DataService
import os

@patch("src.data_fetcher.info_api_client.requests.get")
def test_get_quotes_success(mock_get):
    """
    Test successful get_quotes with a mocked HTTP 200 response.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        [1692400000000, 123.4],
        [1692486400000, 124.1]
    ]
    client = DarwinexInfoAPIClient(api_key="FAKE_KEY")
    data = client.get_quotes("PXQ", "2022-01-01", "2022-01-02")
    assert len(data) == 2
    assert data[0] == [1692400000000, 123.4]

def test_data_service_init():
    """
    Ensure data service can be initialized with a mock API client.
    """
    client = DarwinexInfoAPIClient(api_key="FAKE_KEY")
    ds = DataService(client)
    assert ds.api_client.api_key == "FAKE_KEY"

@patch("src.data_fetcher.info_api_client.requests.get")
def test_fetch_and_save_quotes(mock_get, tmp_path):
    """
    Test fetch_and_save_quotes writes a CSV for each product.
    """
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = [
        [1692400000000, 100.0],
        [1692486400000, 101.0]
    ]

    client = DarwinexInfoAPIClient(api_key="FAKE_KEY")
    ds = DataService(client)
    out_dir = tmp_path / "raw"
    ds.fetch_and_save_quotes(["PXQ"], "2022-01-01", "2022-01-02", save_path=str(out_dir))

    # Check file existence
    files = list(out_dir.glob("*.csv"))
    assert len(files) == 1
    with files[0].open() as f:
        content = f.read()
        assert "100.0" in content
        assert "101.0" in content
