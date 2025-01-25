"""
test_portfolio_service.py
Tests for the PortfolioService logic that excludes fees from the optimization.
"""

import pytest
import pandas as pd
import numpy as np
from src.optimization.portfolio_service import PortfolioService

def test_optimize_distinct_portfolios():
    """
    Provide a small returns df with 2 assets. We expect at least one solution.
    """
    ps = PortfolioService(risk_free_rate=0.0)
    # The method signature in portfolio_service might not have performance_fees now,
    # but we keep a stable scenario:
    np.random.seed(42)
    assetA = 0.001 + np.random.normal(0, 1e-5, 365 * 2)
    assetB = 0.002 + np.random.normal(0, 1e-5, 365 * 2)
    
    df = pd.DataFrame({
        "A": assetA,
        "B": assetB
    })
    # We'll mimic "df" as daily returns for each asset
    results = ps._optimize_distinct_portfolios(df, ["A","B"], num_portfolios=2)
    assert len(results) > 0
    best_sharpe, best_w = results[0]
    assert isinstance(best_sharpe, float)
    assert len(best_w) == 2
    assert abs(sum(best_w) - 1.0) < 1e-8

def test_eq_subset_bruteforce():
    """
    Check the eq-wgts brute force approach with a small set of assets.
    """
    ps = PortfolioService()
    df = pd.DataFrame({
        "A": [0.00, 0.01, 0.02],
        "B": [0.01, -0.005, 0.03],
        "C": [0.002, 0.002, 0.002]
    })
    subset = ps._eq_subset_bruteforce(df, ["A","B","C"])
    # Should return at least 1 asset. Possibly all if it yields best Sharpe.
    assert len(subset) >= 1

def test_filter_assets_less_than_one_year():
    """
    Test that assets with <1 year of data are excluded.
    """
    from datetime import timedelta

    ps = PortfolioService()
    # Suppose we have 2 assets, one with 400 days, one with 100 days
    import pandas as pd

    # Asset X: 400 days
    dates_x = pd.date_range("2022-01-01", periods=400, freq="D")
    prices_x = pd.Series(np.linspace(100, 200, 400), index=dates_x)

    # Asset Y: 100 days
    dates_y = pd.date_range("2022-01-01", periods=100, freq="D")
    prices_y = pd.Series(np.linspace(50, 80, 100), index=dates_y)

    quotes_dict = {
        "X": prices_x,
        "Y": prices_y
    }
    filtered = ps._filter_assets(quotes_dict)
    # Check that X stays if it has total return>0, Y is excluded if <1 year or ret<=0
    assert "X" in filtered
    assert "Y" not in filtered

def test_run_all_tests():
    """
    Placeholder that indicates you can run all tests with pytest from the root directory:
    pytest
    """
    assert True
