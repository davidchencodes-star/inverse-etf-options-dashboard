# Inverse ETF Options Dashboard

A Python Dash web application for systematic short premium selling (short calls and cash-secured puts) on inverse ETFs: **SPXS**, **SQQQ**, **SH**, **SDS**.

## Features

- **VIX Regime Traffic Light** -- Real-time volatility environment indicator
- **S&P 500 & Nasdaq Technical Regime** -- SMA 20/50/100 + RSI(14) with strategy-dependent color signals
- **Inverse ETF Status** -- Quick summary of qualifying options across all 4 ETFs
- **Option Chain with Traffic Lights** -- Filterable table with green/yellow/red indicators per contract
- **Payoff Preview** -- P/L chart at expiration for selected options
- **Configurable Thresholds** -- All rules in `config.yaml` (no code changes needed)

## Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate it
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# Windows CMD:
.\.venv\Scripts\activate.bat
# macOS/Linux:
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the dashboard
python app.py
```

Then open **http://127.0.0.1:8050/** in your browser.

## Data Source

- **Phase 1**: Uses `yfinance` (free, no API key required)
- Provides 15-minute delayed quotes, option chains with IV, and historical data
- Greeks (delta, gamma, theta, vega) computed via Black-Scholes locally

### Future: Swap to Tradier

To switch to Tradier for better options data:
1. Sign up at [tradier.com](https://tradier.com) (free sandbox)
2. Set environment variable: `TRADIER_API_TOKEN=your_token_here`
3. Edit `config.yaml`: change `data_provider: yfinance` to `data_provider: tradier`

## Configuration

Edit `config.yaml` to adjust all thresholds without code changes:

- VIX regime zones (green/yellow/red)
- Annualized return target (default 30%)
- Delta bands for calls and puts
- Liquidity thresholds (min OI, min volume)
- RSI thresholds (overbought/oversold)
- Refresh interval (default 5 minutes)

## Project Structure

```
app.py                    # Main entry point
config.yaml               # All configurable thresholds
data/                     # Data layer (provider, cache, fetch)
calculations/             # Technicals, options analytics, traffic lights
components/               # UI components (KPI cards, table, chart, controls)
callbacks/                # Dash callbacks (refresh, interaction, selection)
assets/                   # Custom CSS
```

## Requirements

- Python 3.12+
- See `requirements.txt` for all dependencies
