"""
test_metrics_calculator.py
Covers various performance metrics from the MetricsCalculator.
"""

import pytest
import pandas as pd
from src.analysis.metrics_calculator import MetricsCalculator

def test_sharpe_ratio_constant_returns():
    """
    Test Sharpe ratio with constant daily returns of 0.1%.
    """
    mc = MetricsCalculator(risk_free_rate=0.0)
    data = pd.Series([0.001]*252)
    sr = mc.sharpe_ratio(data)
    assert sr > 10  # Should be very high for constant returns

def test_max_drawdown():
    """
    Test the max_drawdown function with a simple series.
    """
    mc = MetricsCalculator()
    eq = pd.Series([100, 110, 120, 90])
    dd = mc.max_drawdown(eq)
    # biggest drop is from 120 -> 90 => -25%
    assert dd == -0.25

def test_sortino_ratio_positive_negative():
    """
    Check sortino ratio when we have both positive and negative daily returns.
    """
    mc = MetricsCalculator(risk_free_rate=0.01)
    data = pd.Series([0.01, -0.005, 0.02, 0.0, -0.004] * 50)
    sortino = mc.sortino_ratio(data)
    # Just ensure it's not None or zero
    assert sortino != 0

def test_omega_ratio_above_threshold():
    """
    Test omega ratio for a threshold=0.0 in a mixture of returns.
    """
    mc = MetricsCalculator()
    data = pd.Series([0.01, 0.02, -0.01, 0.005, 0.03, -0.015])
    omega = mc.omega_ratio(data, threshold=0.0)
    # Expect more positive than negative sum
    assert omega > 1
