"""
portfolio_optimizer.py
Contains classes and methods to optimize portfolio weights given return data.
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize

class PortfolioOptimizer:
    """
    Performs portfolio weight optimization based on an objective function (e.g., maximizing Sharpe).

    Attributes:
        performance_fees (float): Performance fee rate to account for.
        leverage (float): Leverage factor.
    """

    def __init__(self, performance_fees=0.2, leverage=1.0):
        """
        :param performance_fees: Performance fee rate (e.g., 0.2 for 20%).
        :param leverage: Leverage factor.
        """
        self.performance_fees = performance_fees
        self.leverage = leverage

    def optimize_weights(self, returns_dict, optimization_goal="max_sharpe"):
        """
        Find optimal weights for a set of assets according to the desired goal.

        :param returns_dict: A dictionary {productName: pd.Series of returns}.
        :param optimization_goal: The optimization goal, e.g. "max_sharpe".
        :return: A pd.Series of weights for each asset.
        """
        returns_df = pd.DataFrame(returns_dict)

        def objective(weights):
            """
            Objective function for portfolio optimization (e.g. maximize Sharpe => minimize negative Sharpe).
            """
            portfolio_returns = (returns_df * weights).sum(axis=1)
            # Adjust for fees and leverage
            net_returns = portfolio_returns * self.leverage - self.performance_fees * abs(portfolio_returns)
            mean_ret = net_returns.mean() * 252
            std_ret = net_returns.std() * np.sqrt(252)
            if std_ret == 0:
                return 1e6
            return -(mean_ret / std_ret)

        num_assets = len(returns_dict.keys())
        init_weights = np.array([1.0 / num_assets] * num_assets)
        bounds = [(0.0, 1.0)] * num_assets
        constraints = [
            {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        ]

        result = minimize(objective, init_weights, method="SLSQP", bounds=bounds, constraints=constraints)
        if not result.success:
            print("Optimization failed:", result.message)

        assets = list(returns_dict.keys())
        return pd.Series(result.x, index=assets)
