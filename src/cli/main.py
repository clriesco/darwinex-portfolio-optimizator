"""
main.py
CLI entry point for Darwinex Portfolio Optimization.

Subcommands:
- download: Download raw files (with optional throttling).
- calculate-fees: Preprocess raw files to subtract fees from positive returns.
- best-portfolios: Generate best portfolios with optional max-darwins constraint.
"""

import argparse
from datetime import datetime

from src.data_fetcher.info_api_client import DarwinexInfoAPIClient
from src.data_fetcher.data_service import DataService
from src.optimization.portfolio_service import PortfolioService

def main():
    """
    Main CLI entry point. Parses arguments and calls the relevant function.
    """
    parser = argparse.ArgumentParser(description="CLI for Darwinex Portfolio Optimization (Fees preprocessed).")
    subparsers = parser.add_subparsers(dest="command")

    # Subcommand: download
    parser_download = subparsers.add_parser("download", help="Download DARWIN quotes from Darwinex Info API")
    parser_download.add_argument("-d", "--darwins", nargs="+", required=True,
                                 help="List of DARWIN symbols to download (required).")
    parser_download.add_argument("-s", "--start", help="Start date (YYYY-MM-DD). Optional. Default=2022-01-01")
    parser_download.add_argument("-e", "--end", help="End date (YYYY-MM-DD). Optional. Default=today")
    parser_download.add_argument("--save-path", default="data/raw", help="Directory to save raw CSV files. Optional.")

    # Subcommand: calculate-fees
    parser_fees = subparsers.add_parser("calculate-fees", help="Preprocess raw files to subtract fees from positive returns.")
    parser_fees.add_argument("--fee-rate", type=float, default=0.2,
                             help="Performance fee rate (0.2 = 20%). Optional. Default=0.2")
    parser_fees.add_argument("--raw-path", default="data/raw",
                             help="Directory with raw CSV files to process. Optional. Default='data/raw'")
    parser_fees.add_argument("--processed-path", default="data/processed",
                             help="Directory to store processed CSV files. Optional. Default='data/processed'")

    # Subcommand: best-portfolios
    parser_best = subparsers.add_parser("best-portfolios",
                                        help="Generate best portfolios from processed data (no fees at portfolio level).")
    parser_best.add_argument("-d", "--darwins", nargs="+",
                             help="List of product names. If omitted, discover from CSV in save-path.")
    parser_best.add_argument("-s", "--start", help="Start date (YYYY-MM-DD). Optional. Default=2022-01-01")
    parser_best.add_argument("-e", "--end", help="End date (YYYY-MM-DD). Optional. Default=today")
    parser_best.add_argument("--save-path", help="Directory with CSV files. Optional. Default='data/processed'")
    parser_best.add_argument("-x", "--num-portfolios", type=int, help="Number of distinct solutions. Optional. Default=10")
    parser_best.add_argument("--leverage", type=float, help="Leverage factor. Optional. Default=1.0")
    parser_best.add_argument("--plot-individual", action="store_true",
                             help="Plot individual assets as well. Optional.")
    parser_best.add_argument("--equal-weights", action="store_true",
                             help="If set, finds the best subset under equal weighting. Optional.")
    parser_best.add_argument("--max-darwins", type=int,
                             help="Maximum number of assets in a final portfolio. Optional. No limit if not specified.")

    args = parser.parse_args()

    if args.command == "download":
        start_date = args.start if args.start else "2022-01-01"
        end_date = args.end if args.end else datetime.now().strftime("%Y-%m-%d")
        api_client = DarwinexInfoAPIClient()
        data_service = DataService(api_client)
        data_service.fetch_and_save_quotes(args.darwins, start_date, end_date, args.save_path)

    elif args.command == "calculate-fees":
        from src.data_fetcher.fees_preprocessor import FeesPreprocessor
        fee_tool = FeesPreprocessor(fee_rate=args.fee_rate)
        fee_tool.process_all_files(args.raw_path, args.processed_path)

    elif args.command == "best-portfolios":
        start = args.start if args.start else "2022-01-01"
        end = args.end if args.end else datetime.now().strftime("%Y-%m-%d")
        service = PortfolioService()
        service.generate_best_portfolios(
            darwins=args.darwins,
            start=start,
            end=end,
            num_portfolios=args.num_portfolios,
            plot_individual=args.plot_individual,
            save_path=args.save_path if args.save_path else "data/processed",
            leverage=args.leverage,
            equal_weights=args.equal_weights,
            max_darwins=args.max_darwins
        )

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
