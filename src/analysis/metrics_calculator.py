"""
metrics_calculator.py
Provides various performance metrics for daily returns or equity curves.
"""

import pandas as pd
import numpy as np

class MetricsCalculator:
    """
    Calculates performance metrics such as Sharpe, Sortino, Max Drawdown, etc.

    Attributes:
        risk_free_rate (float): annual risk-free rate in decimal form.
    """

    def __init__(self, risk_free_rate=0.0):
        """
        :param risk_free_rate: Annual risk-free rate for metric calculations.
        """
        self.risk_free_rate = risk_free_rate

    def daily_returns(self, prices: pd.Series) -> pd.Series:
        """
        Convert a price series to daily returns. Fills NaN with 0.0.

        :param prices: A pd.Series of prices.
        :return: A pd.Series of daily returns.
        """
        return prices.pct_change().fillna(0.0)

    def sharpe_ratio(self, returns: pd.Series) -> float:
        """
        Annualized Sharpe ratio.

        :param returns: A pd.Series of daily returns.
        :return: Sharpe ratio as float.
        """
        excess = returns - self.risk_free_rate / 252
        std = returns.std()
        if std == 0:
            return 0.0
        return (excess.mean() / std) * np.sqrt(252)

    def sortino_ratio(self, returns: pd.Series) -> float:
        """
        Annualized Sortino ratio.

        :param returns: A pd.Series of daily returns.
        :return: Sortino ratio as float.
        """
        excess = returns - self.risk_free_rate / 252
        negative = returns[returns < 0]
        d_std = negative.std()
        if d_std == 0:
            return 0.0
        return (excess.mean() / d_std) * np.sqrt(252)

    def max_drawdown(self, equity: pd.Series) -> float:
        """
        Maximum drawdown from an equity curve.

        :param equity: A pd.Series representing cumulative equity.
        :return: The minimum (negative) drawdown.
        """
        roll_max = equity.cummax()
        dd = (equity - roll_max) / roll_max
        return dd.min()

    def total_return(self, equity: pd.Series) -> float:
        """
        Total return over the entire equity curve.

        :param equity: A pd.Series representing cumulative equity.
        :return: decimal form e.g. 0.5 for +50%
        """
        return (equity.iloc[-1] / equity.iloc[0]) - 1

    def longest_drawdown_period(self, equity: pd.Series) -> int:
        """
        Returns the longest drawdown (in days).

        :param equity: A pd.Series representing cumulative equity.
        :return: integer, max consecutive days in drawdown.
        """
        roll_max = equity.cummax()
        dd = (equity - roll_max) / roll_max
        is_dd = dd < 0
        dd_periods = is_dd.astype(int).groupby((is_dd != is_dd.shift()).cumsum()).cumsum()
        return dd_periods.max()

    def calmar_ratio(self, equity: pd.Series) -> float:
        """
        Calmar ratio = annual return / max drawdown

        :param equity: equity curve
        :return: Calmar ratio float
        """
        days = len(equity)
        if days < 2:
            return 0.0
        ann_return = (equity.iloc[-1] / equity.iloc[0]) ** (252 / days) - 1
        mdd = self.max_drawdown(equity)
        if mdd == 0:
            return np.inf
        return ann_return / abs(mdd)

    def omega_ratio(self, returns: pd.Series, threshold=0.0) -> float:
        """
        Omega ratio above a threshold.

        :param returns: daily returns
        :param threshold: threshold for gains/losses
        :return: Omega ratio
        """
        above = returns[returns > threshold] - threshold
        below = threshold - returns[returns < threshold]
        if below.sum() == 0:
            return np.inf
        return above.sum() / below.sum()
