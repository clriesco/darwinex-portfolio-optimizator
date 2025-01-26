# Darwinex Portfolio Optimization

This project provides a **SOLID**-structured application to:

1. **Download** historical quotes from the Darwinex Info API (v2.1).
2. **Preprocess** each raw CSV file to **subtract performance fees** in a simplified model, generating new files in `data/processed`.
3. **Build** multiple portfolios (distinct or equal-weights best subset) **without** applying any performance fees at portfolio level (since fees were already subtracted in the `data/processed` files).
4. **Filter** out assets with less than 1 year of data or non-positive total return.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
  - [Download data](#1-download-data)
  - [Calculate fees in data/raw](#2-calculate-fees-in-dataraw)
  - [Generate best portfolios](#3-generate-best-portfolios)
- [Project Structure](#project-structure)
- [License](#license)

## Installation

1. **Clone** this repository from GitHub:

   ```bash
   git clone https://github.com/clriesco/darwinex_portfolio_optimizator.git
   cd darwinex_portfolio_optimizator
   ```

2.  **Create** a virtual environment and activate it:
    
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Unix-like systems
    # or
    venv\Scripts\activate  # On Windows
    ```
    
3.  **Install** dependencies:
    
    ```bash
    pip install -r requirements.txt
    ```
    
4.  **Create** your `.env` file based on `.env.example`:
    
    ```bash
    cp .env.example .env
    ```
    
    Then open `.env` and place your **Darwinex Info API Key** as follows:
    
    ```bash
    DARWINEX_API_KEY="YOUR_DARWINEX_API_KEY"
    ```
    
    > You can obtain your Darwinex Info API key [here](https://www.darwinex.com/es/data/darwin-api).
    
5.  _(Optional)_ Throttling:  
    If you want to respect the **10 requests/min** limit, modify existing env variable.
    
    ```bash
    DARWINEX_THROTTLING_SECONDS=6.0
    ```
    
    By default, it's `6.0` if not specified.
    

Usage
-----

```bash
python -m src.cli.main --help
```

### download

**Usage**:

```bash
python -m src.cli.main download \
  -d PXQ JBC \
  --start 2022-01-01 \
  --end 2022-06-30 \
  --save-path data/raw
```

**Arguments**:

*   `-d/--darwins`: **Required**. Space-separated DARWIN symbols.
*   `-s/--start`: Optional. Start date in `YYYY-MM-DD`. Defaults to `2022-01-01`.
*   `-e/--end`: Optional. End date in `YYYY-MM-DD`. Defaults to today.
*   `--save-path`: Optional. Defaults to `data/raw`.

**Notes**:

*   If environment variable `DARWINEX_THROTTLING_SECONDS` is set (e.g. `6.0`), the script will pause that many seconds between each request to avoid surpassing 10 req/min.

### calculate-fees

**Usage**:

```bash
python -m src.cli.main calculate-fees \
  --fee-rate 0.2 \
  --raw-path data/raw \
  --processed-path data/processed
```

**Arguments**:

*   `--fee-rate`: Optional. Default=0.2 (20%). Subtracted from daily positive returns.
*   `--raw-path`: Optional. Default=`data/raw`. Directory containing the original CSV files.
*   `--processed-path`: Optional. Default=`data/processed`. Directory to store the new CSV files with fees subtracted.

### best-portfolios

**Usage**:

```bash
python -m src.cli.main best-portfolios \
  -d PXQ JBC \
  --start 2022-01-01 \
  --end 2022-06-30 \
  --save-path data/processed \
  --num-portfolios 5 \
  --plot-individual \
  --max-darwins 8
```

**Arguments**:

*   `-d/--darwins`: Optional. Space-separated symbols. If not provided, it discovers them from CSV in `--save-path`.
*   `-s/--start`: Optional. Default=`2022-01-01`.
*   `-e/--end`: Optional. Default=today.
*   `--save-path`: Optional. Default=`data/processed`. Where to read CSV files from.
*   `-x/--num-portfolios`: Optional. Number of distinct solutions to keep. Default=10.
*   `--leverage`: Optional. Default=1.0. Scales daily returns by this factor.
*   `--plot-individual`: If present, also plot each asset's equity curve.
*   `--equal-weights`: If present, tries to find the best subset under equal weights approach.
*   `--max-darwins`: Optional. Maximum number of assets allowed in the final portfolio. If omitted, no limit.

**Notes**:

*   This subcommand does **not** apply performance fees in the optimization or final equity. It is assumed you have already subtracted fees with `calculate-fees`.


Project Structure
-----------------

```bash
darwinex_portfolio_optimization/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── setup.py
├── data/
│   ├── raw/
│   └── processed/
├── src/
│   ├── cli/main.py
│   ├── data_fetcher/info_api_client.py
│   ├── data_fetcher/data_service.py
│   ├── data_fetcher/fees_preprocessor.py
│   ├── analysis/metrics_calculator.py
│   ├── optimization/portfolio_service.py
│   ├── optimization/constraints.py
│   └── visualization/plotter.py
└── tests/
    └── test_data_fetcher.py
    └── test_metrics_calculator.py
    └── test_portfolio_service.py
```

License
-------

```bash
Copyright 2025 - Charly López

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---
