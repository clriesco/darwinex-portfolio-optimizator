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
    

Usage
-----

```bash
python -m src.cli.main --help
```

### 1\. Download data

```bash
python -m src.cli.main download \
  --darwins PXQ JBC \
  --start 2022-01-01 \
  --end 2022-06-30 \
  --save-path data/raw
```

### 2\. Calculate fees in data/raw

```bash
python -m src.cli.main calculate-fees \
  --fee-rate 0.2 \
  --raw-path data/raw \
  --processed-path data/processed
```

*   This reads each CSV in `data/raw`, applies a daily approach to subtract fees from positive returns, and saves the resulting prices to `data/processed`.

### 3\. Generate best portfolios

```bash
python -m src.cli.main best-portfolios \
  --darwins PXQ JBC \
  --start 2022-01-01 \
  --end 2022-06-30 \
  --save-path data/processed \
  --num-portfolios 5 \
  --plot-individual
```

*   This **does not** apply performance fees. Leverage is still optional (`--leverage 2.0`).
*   Assets with <1 year of data or total return ≤ 0 are filtered out.

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
