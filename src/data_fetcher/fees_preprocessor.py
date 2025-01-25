"""
fees_preprocessor.py
Implements a three-step process for applying daily performance fees to raw price data:
1) Compute daily returns,
2) Subtract fee_rate from positive returns,
3) Rebuild the price series from the adjusted daily returns.
"""

import os
import pandas as pd

class FeesPreprocessor:
    """
    FeesPreprocessor applies a simplified daily fee approach in three steps:
      1) daily_return = (close_t / close_{t-1}) - 1,
      2) If daily_return > 0, daily_return *= (1 - fee_rate),
      3) Reconstruct close(t) = close(t-1) * (1 + daily_return).

    The resulting price series is saved to new CSVs in data/processed.
    """

    def __init__(self, fee_rate=0.2):
        """
        :param fee_rate: Decimal representation of performance fee (e.g. 0.2 = 20%).
        """
        self.fee_rate = fee_rate

    def process_all_files(self, raw_path, processed_path):
        """
        Reads all CSV files from raw_path, applies the three-step fee logic,
        and saves the new price series in processed_path.

        :param raw_path: Directory containing raw CSV files (with columns date, close).
        :param processed_path: Directory to store the fees-adjusted CSV files.
        """
        if not os.path.exists(processed_path):
            os.makedirs(processed_path)

        csv_files = [f for f in os.listdir(raw_path) if f.endswith(".csv")]
        for fname in csv_files:
            full_in = os.path.join(raw_path, fname)
            df = pd.read_csv(full_in, parse_dates=["date"])
            if len(df) < 2:
                print(f"[WARN] Not enough data in {fname}. Skipped.")
                continue

            # Ensure data is sorted by date
            df.sort_values("date", inplace=True)
            df.reset_index(drop=True, inplace=True)

            processed_df = self._apply_fee_process(df)
            out_name = fname  # keep the same filename
            out_full = os.path.join(processed_path, out_name)
            processed_df.to_csv(out_full, index=False)
            print(f"[INFO] Fees processed for {fname}, new file: {out_full}")

    def _apply_fee_process(self, df):
        """
        Apply the three-step fee process to a single DataFrame.

        :param df: DataFrame with columns ['date', 'close'] sorted by date.
        :return: A new DataFrame with the same columns, but 'close' reflecting the net effect of fees.
        """
        df = df.copy()

        # 1) daily_returns: for t >= 1 => r_t = close_t / close_{t-1} - 1
        daily_returns = []
        daily_returns.append(0.0)  # The first day has no prior day, so daily return = 0

        for i in range(1, len(df)):
            prev_price = df.loc[i - 1, "close"]
            curr_price = df.loc[i, "close"]
            raw_ret = (curr_price / prev_price) - 1.0
            daily_returns.append(raw_ret)

        # 2) subtract fee_rate from positive returns
        adj_returns = []
        for ret in daily_returns:
            if ret > 0:
                net_ret = ret * (1 - self.fee_rate)
            else:
                net_ret = ret
            adj_returns.append(net_ret)

        # 3) rebuild the price series: new_close[0] = df.close[0], new_close[t] = new_close[t-1] * (1 + adj_returns[t])
        new_close = []
        new_close.append(df.loc[0, "close"])  # first day remains the same

        for i in range(1, len(df)):
            new_price = new_close[i - 1] * (1.0 + adj_returns[i])
            new_close.append(new_price)

        out_df = pd.DataFrame({
            "date": df["date"],
            "close": new_close
        })
        return out_df
