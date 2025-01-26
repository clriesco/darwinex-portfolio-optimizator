"""
portfolio_service.py
Provides a high-level service for:
1) Discovering which CSV files to load (if not specified),
2) Filtering out assets with <1 year of data or non-positive returns,
3) Plotting correlation,
4) Generating portfolios (distinct or best equal-weights subset) WITHOUT FEES,
   since fees are assumed to be subtracted in the data/processed step.
"""

import os
import re
import numpy as np
import pandas as pd
from datetime import datetime
from scipy.optimize import minimize
from random import uniform

from src.analysis.metrics_calculator import MetricsCalculator
from src.optimization.constraints import get_exposure_bounds
from src.visualization.plotter import Plotter

class PortfolioService:
    """
    PortfolioService orchestrates:
      - Discovery of CSV data,
      - Filtering out assets with total return <= 0 or <1 year of data,
      - Plotting correlation,
      - Optimizing or finding best subset (equal-weights),
      - WITHOUT applying any performance fees in the objective or equity curve.

    Attributes:
        risk_free_rate (float): annual risk-free rate in decimal form.
        max_random_tries_factor (int): factor to multiply by num_portfolios for random restarts.
        leverage (float): leverage factor that scales daily returns, default=1.0
    """

    def __init__(self, risk_free_rate=0.02, max_random_tries_factor=30):
        """
        :param risk_free_rate: annual risk-free rate for Sharpe, etc.
        :param max_random_tries_factor: factor for random restarts.
        """
        self.risk_free_rate = risk_free_rate
        self.max_random_tries_factor = max_random_tries_factor
        self.leverage = 1.0

    def generate_best_portfolios(
        self,
        darwins=None,
        start=None,
        end=None,
        num_portfolios=None,
        plot_individual=False,
        save_path=None,
        leverage=None,
        equal_weights=False,
        max_darwins=None
    ):
        """
        Main entry point to generate best portfolios from data.

        :param darwins: List of symbols or None. If None, discover from CSV in save_path.
        :param start: Start date in 'YYYY-MM-DD'. If None, defaults to '2022-01-01'.
        :param end: End date in 'YYYY-MM-DD'. If None, defaults to today.
        :param num_portfolios: Number of distinct solutions, default=10 if not specified.
        :param plot_individual: If True, show each asset's equity curve.
        :param save_path: Directory with CSV files, default='data/processed'.
        :param leverage: Leverage factor, default=1.0
        :param equal_weights: If True, find best subset for eq-wgts instead of distinct optimization.
        :param max_darwins: If not None, limit the final portfolio to at most `max_darwins` assets.
        """
        if not start:
            start = "2022-01-01"
        if not end:
            end = datetime.now().strftime("%Y-%m-%d")
        if not num_portfolios:
            num_portfolios = 10
        if not save_path:
            save_path = "data/processed"
        if leverage is None:
            leverage = 1.0

        self.leverage = leverage

        final_darwins, discovered_map = self._resolve_darwins(darwins, start, end, save_path)
        if len(final_darwins) == 0:
            print("[ERROR] No valid DARWIN data found.")
            return

        quotes_dict = self._load_prices(final_darwins, discovered_map, start, end, save_path)
        if len(quotes_dict) == 0:
            print("[ERROR] No data loaded. Aborting.")
            return

        # Filter out assets (non-positive or <1 year)
        filtered_dict = self._filter_assets(quotes_dict)
        if len(filtered_dict) == 0:
            print("[ERROR] All assets are either non-positive or have <1 year of data.")
            return

        # Build daily returns
        mc = MetricsCalculator(risk_free_rate=self.risk_free_rate)
        returns_map = {}
        for sym, price_ser in filtered_dict.items():
            ret = mc.daily_returns(price_ser)
            returns_map[sym] = ret

        returns_df = pd.DataFrame(returns_map).fillna(0.0)
        final_symbols = list(filtered_dict.keys())

        # Plot correlation
        plotter = Plotter(style="whitegrid")
        corr_matrix = returns_df.corr()
        plotter.plot_correlation_heatmap(corr_matrix, title="Correlation Matrix of Selected Assets")

        # If user wants best subset with eq weights
        if equal_weights:
            print("[INFO] Finding best subset under equal weights.")
            best_subset = self._generate_equal_weights_best_subset(returns_df, final_symbols)
            if not best_subset or len(best_subset) == 0:
                print("[WARN] No subset found for equal weights.")
                return

            # If max_darwins is set, limit the subset
            if max_darwins is not None and len(best_subset) > max_darwins:
                # Chose a criterion to limit the subset
                # for example, by average returns
                print(f"[INFO] best_subset has {len(best_subset)} assets, limiting to {max_darwins} by average returns.")
                mean_map = {}
                for sym in best_subset:
                    mean_map[sym] = returns_df[sym].mean()
                # Order by mean return
                sorted_symbols = sorted(best_subset, key=lambda s: mean_map[s], reverse=True)
                best_subset = sorted_symbols[:max_darwins]

            print(f"[INFO] Final subset for eq-wgts: {best_subset}")
            eq_w = np.ones(len(best_subset)) / len(best_subset)
            self._evaluate_and_plot_single_portfolio(
                eq_w, best_subset, returns_df, mc, plotter, plot_individual, tag="Best Equal-Weights Subset"
            )
            return

        # Otherwise do distinct optimization
        best_portfolios = self._optimize_distinct_portfolios(returns_df, final_symbols, num_portfolios)
        if len(best_portfolios) == 0:
            print("[WARN] No distinct portfolios found.")
            return
        
        if max_darwins is not None:
            print(f"[INFO] Limiting final portfolios to at most {max_darwins} assets.")
            filtered_results = []
            for sharpe_val, w in best_portfolios:
                # Count how many assets have weight>1e-4
                active_assets_idx = [i for i, val in enumerate(w) if val > 1e-4]
                if len(active_assets_idx) <= max_darwins:
                    filtered_results.append((sharpe_val, w))
                else:
                    # Reassign weights to top max_darwins but keep sharpe ratio
                    w_copy = w.copy()
                    # Order by weight
                    sorted_idx = sorted(range(len(w)), key=lambda i: w[i], reverse=True)
                    keep_idx = sorted_idx[:max_darwins]
                    zero_idx = sorted_idx[max_darwins:]
                    for i in zero_idx:
                        w_copy[i] = 0.0
                    # Rebalance

                    total_sum = sum(w_copy)
                    if total_sum > 0:
                        w_copy = w_copy / total_sum

                    filtered_results.append((sharpe_val, w_copy))
            best_portfolios = filtered_results

        print(f"Top {len(best_portfolios)} DISTINCT portfolios:")
        for i, (sharpe_val, w) in enumerate(best_portfolios, start=1):
            print(f"Portfolio #{i}")
            print(f"  Estimated Sharpe: {sharpe_val:.4f}")
            for d, wval in zip(final_symbols, w):
                print(f"    {d}: {wval*100:.2f}%")
            print("")

        for i, (sharpe_val, w) in enumerate(best_portfolios, start=1):
            tag = f"Portfolio #{i} (Sharpe ~ {sharpe_val:.2f})"
            self._evaluate_and_plot_single_portfolio(w, final_symbols, returns_df, mc, plotter, plot_individual, tag)

    def _optimize_distinct_portfolios(self, returns_df, symbols, num_portfolios):
        """
        Multiple random restarts to find distinct sets with sum(weights)=1,
        bounds in [1/(2N), 2/N], and no fees. Leverage is stored in self.leverage.

        :param returns_df: DataFrame of daily returns.
        :param symbols: List of symbols.
        :param num_portfolios: Number of solutions to keep.
        :return: list of (sharpe_val, weights_array).
        """
        n_assets = len(symbols)
        if n_assets < 1:
            return []

        from src.optimization.constraints import get_exposure_bounds
        bounds = get_exposure_bounds(n_assets)
        constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

        def objective(weights):
            daily_port = (returns_df[symbols] * weights).sum(axis=1)
            daily_net = daily_port * self.leverage  # no fees
            mean_ret = daily_net.mean() * 252
            std_ret = daily_net.std() * np.sqrt(252)
            if std_ret == 0:
                return 1e6
            return -(mean_ret / std_ret)

        best_portfolios = []
        seen_sets = set()
        tries = num_portfolios * self.max_random_tries_factor

        for _ in range(tries):
            w0 = []
            for (mn, mx) in bounds:
                val = np.random.uniform(mn, mx)
                w0.append(val)
            w0 = np.array(w0)
            w0 /= w0.sum()

            res = minimize(objective, w0, method="SLSQP", bounds=bounds, constraints=constraints)
            if not res.success:
                continue

            est_sharpe = -res.fun
            w = res.x
            active_set = frozenset([symbols[i] for i, v in enumerate(w) if v > 1e-4])
            if active_set not in seen_sets:
                best_portfolios.append((est_sharpe, w))
                seen_sets.add(active_set)

        best_portfolios.sort(key=lambda x: x[0], reverse=True)
        return best_portfolios[:num_portfolios]

    def _generate_equal_weights_best_subset(self, returns_df, symbols):
        """
        Finds best subset for eq-wgts. If #assets <=15, brute force. Else use backward elimination.

        :param returns_df: daily returns DataFrame
        :param symbols: list of symbols
        :return: list of chosen symbols
        """
        M = len(symbols)
        if M < 1:
            return []

        if M <= 15:
            return self._eq_subset_bruteforce(returns_df, symbols)
        else:
            return self._eq_subset_backward_elimination(returns_df, symbols)

    def _eq_subset_bruteforce(self, returns_df, symbols):
        """
        Enumerate subsets, no fees, just leverage.

        :param returns_df: DataFrame
        :param symbols: list
        :return: best subset
        """
        from itertools import combinations

        best_sharpe = float("-inf")
        best_subset = []

        def compute_sharpe(sub):
            if not sub:
                return None
            w = 1.0 / len(sub)
            daily_port = returns_df[sub].sum(axis=1) * w
            daily_net = daily_port * self.leverage
            mean_ret = daily_net.mean() * 252
            std_ret = daily_net.std() * np.sqrt(252)
            if std_ret == 0:
                return None
            return mean_ret / std_ret

        for size in range(1, len(symbols)+1):
            for combo in combinations(symbols, size):
                subset_sym = list(combo)
                shr = compute_sharpe(subset_sym)
                if shr is not None and shr > best_sharpe:
                    best_sharpe = shr
                    best_subset = subset_sym
        return best_subset

    def _eq_subset_backward_elimination(self, returns_df, symbols):
        """
        Start with all, remove one asset if it improves Sharpe, until no improvement.
        :param returns_df: DataFrame
        :param symbols: list
        :return: final subset
        """
        current_set = list(symbols)

        def eq_sharpe(sub):
            if len(sub) < 1:
                return float("-inf")
            w = 1.0 / len(sub)
            daily_port = returns_df[sub].sum(axis=1) * w
            daily_net = daily_port * self.leverage
            mean_ret = daily_net.mean() * 252
            std_ret = daily_net.std() * np.sqrt(252)
            if std_ret == 0:
                return float("-inf")
            return mean_ret / std_ret

        best_val = eq_sharpe(current_set)
        improved = True
        while improved and len(current_set) > 1:
            improved = False
            for sym in current_set:
                trial = [x for x in current_set if x != sym]
                test_val = eq_sharpe(trial)
                if test_val > best_val:
                    best_val = test_val
                    current_set = trial
                    improved = True
                    break
        return current_set

    def _evaluate_and_plot_single_portfolio(self, weights, symbols, returns_df, mc, plotter, plot_individual, tag):
        """
        Build daily net with leverage (no fees), compute metrics, plot equity.

        :param weights: array of weights
        :param symbols: list of symbols
        :param returns_df: daily returns
        :param mc: MetricsCalculator
        :param plotter: Plotter
        :param plot_individual: bool
        :param tag: str for print/plot
        """
        daily_port = (returns_df[symbols] * weights).sum(axis=1)
        daily_net = daily_port * self.leverage
        equity = (1 + daily_net).cumprod() * 100

        p_sharpe = mc.sharpe_ratio(daily_net)
        p_sortino = mc.sortino_ratio(daily_net)
        p_return = equity.iloc[-1] / equity.iloc[0] - 1
        p_mdd = mc.max_drawdown(equity)
        p_dd_days = mc.longest_drawdown_period(equity)
        p_calmar = mc.calmar_ratio(equity)
        p_omega = mc.omega_ratio(daily_net)

        print(f"{tag} metrics:")
        print(f"  Sharpe Ratio      : {p_sharpe:.3f}")
        print(f"  Sortino Ratio     : {p_sortino:.3f}")
        print(f"  Max Drawdown      : {p_mdd*100:.2f}%")
        print(f"  Total Return      : {p_return*100:.2f}%")
        print(f"  Longest DD Period : {p_dd_days} days")
        print(f"  Calmar Ratio      : {p_calmar:.3f}")
        print(f"  Omega Ratio       : {p_omega:.3f}")
        print("")

        plotter.plot_portfolio_evolution(equity, title=tag)

        if plot_individual:
            eq_dict = {}
            for d, wval in zip(symbols, weights):
                indiv_ret = returns_df[d] * wval
                indiv_net = indiv_ret * self.leverage
                eq_dict[d] = (1 + indiv_net).cumprod() * 100
            plotter.plot_individual_equities(eq_dict)

    def _resolve_darwins(self, darwins, start, end, save_path):
        """
        If darwins is provided, return them. Else discover from CSV in save_path.

        :param darwins: optional list of symbols
        :param start: not used here, but part of signature
        :param end: not used
        :param save_path: folder
        :return: (list_of_symbols, dict {sym:filename})
        """
        if darwins and len(darwins) > 0:
            return darwins, {}

        if not os.path.exists(save_path):
            print(f"[ERROR] Directory {save_path} does not exist.")
            return [], {}

        csv_files = [f for f in os.listdir(save_path) if f.endswith(".csv")]
        if len(csv_files) == 0:
            print(f"[ERROR] No CSV files in {save_path}.")
            return [], {}

        pattern = re.compile(r"^(?P<darwin>[A-Z0-9]+)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2}).csv$")
        file_dict = {}
        for fname in csv_files:
            match = pattern.match(fname)
            if match:
                dname = match.group("darwin")
                file_dict.setdefault(dname, []).append(fname)
            else:
                print(f"[WARN] File '{fname}' doesn't match naming convention. Skipped.")

        discovered_map = {}
        final_list = []
        for dname, flist in file_dict.items():
            flist.sort()
            chosen = flist[-1]
            discovered_map[dname] = chosen
            final_list.append(dname)

        return final_list, discovered_map

    def _load_prices(self, darwins, discovered_map, start, end, save_path):
        """
        Load CSV for each darwin. If discovered_map has it, use that file, else build {d}_{start}_{end}.csv

        :param darwins: list of symbols
        :param discovered_map: dict {sym: filename}
        :param start: str
        :param end: str
        :param save_path: directory
        :return: dict {sym: price_series}
        """
        quotes_dict = {}
        for d in darwins:
            if d in discovered_map:
                chosen = discovered_map[d]
            else:
                chosen = f"{d}_{start}_{end}.csv"
            full_path = os.path.join(save_path, chosen)
            if not os.path.exists(full_path):
                print(f"[WARN] File not found: {full_path}. Skipped {d}.")
                continue

            df = pd.read_csv(full_path, parse_dates=["date"], index_col="date").sort_index()
            quotes_dict[d] = df["close"]
        return quotes_dict

    def _filter_assets(self, quotes_dict):
        """
        Filter out assets with total return <= 0 or < 1 year of data.

        :param quotes_dict: {sym: price_series}
        :return: filtered dict
        """
        result = {}
        for sym, series in quotes_dict.items():
            if len(series) < 2:
                continue
            total_ret = (series.iloc[-1] / series.iloc[0]) - 1
            if total_ret <= 0:
                continue
            first_date = series.index[0]
            last_date = series.index[-1]
            days_diff = (last_date - first_date).days
            if days_diff < 365:
                continue
            result[sym] = series
        return result
