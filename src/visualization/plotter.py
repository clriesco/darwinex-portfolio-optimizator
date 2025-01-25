"""
plotter.py
Responsible for plotting correlation, equity curves, etc. using seaborn/matplotlib.
"""

import matplotlib.pyplot as plt
import seaborn as sns

class Plotter:
    """
    Provides methods to plot correlation heatmaps, portfolio evolutions, and return distributions.
    """

    def __init__(self, style="whitegrid"):
        """
        :param style: Seaborn style for consistent plotting, e.g. 'whitegrid'
        """
        sns.set_style(style)

    def plot_correlation_heatmap(self, corr_matrix, title="Correlation Matrix"):
        """
        Plots a heatmap of the correlation matrix WITHOUT numeric annotations.

        :param corr_matrix: DataFrame correlation matrix
        :param title: Plot title
        """
        plt.figure(figsize=(8,6))
        sns.heatmap(corr_matrix, annot=False, cmap="RdBu", center=0)
        plt.title(title)
        plt.show()

    def plot_portfolio_evolution(self, portfolio_equity, title="Portfolio Evolution"):
        """
        Plot an equity curve.

        :param portfolio_equity: A pd.Series of equity over time.
        :param title: Title for the plot.
        """
        plt.figure(figsize=(10,6))
        sns.lineplot(x=portfolio_equity.index, y=portfolio_equity.values, label="Portfolio")
        plt.title(title)
        plt.xlabel("Date")
        plt.ylabel("Equity")
        plt.legend()
        plt.show()

    def plot_individual_equities(self, equities_dict):
        """
        Plots equity curves for multiple assets in a single figure.

        :param equities_dict: dict {asset: pd.Series of equity}
        """
        plt.figure(figsize=(10,6))
        for asset, eq in equities_dict.items():
            sns.lineplot(x=eq.index, y=eq.values, label=asset)
        plt.title("Individual Assets Evolution")
        plt.xlabel("Date")
        plt.ylabel("Equity")
        plt.legend()
        plt.show()
