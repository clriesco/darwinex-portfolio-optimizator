"""
constraints.py
Defines any specialized constraints or methods to build them for the portfolio optimization.
"""

def get_exposure_bounds(num_assets: int):
    """
    Returns a list of (min_w, max_w) for each asset,
    such that min_w = 1/(2N) and max_w = 2/N.
    """
    min_w = 1.0 / (2 * num_assets)
    max_w = 2.0 / num_assets
    return [(min_w, max_w)] * num_assets
