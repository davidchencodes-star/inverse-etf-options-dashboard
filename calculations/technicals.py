"""
Technical indicator calculations.

Computes SMA (20/50/100) and RSI(14) from historical daily price data.
"""

from typing import Any

import pandas as pd

def compute_sma(prices: pd.Series, window: int) -> pd.Series:
    """
    Compute Simple Moving Average.

    Args:
        prices: Series of closing prices (indexed by date).
        window: Number of periods for the moving average.

    Returns:
        Series of SMA values.
    """
    return prices.rolling(window=window, min_periods=window).mean()


def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """
    Compute Relative Strength Index.

    Uses the standard Wilder smoothing method (exponential moving average).

    Args:
        prices: Series of closing prices (indexed by date).
        period: RSI look-back period (default 14).

    Returns:
        Series of RSI values (0-100).
    """
    delta = prices.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))

    return rsi


def get_index_technicals(historical_df: pd.DataFrame) -> dict[str, Any]:
    """
    Compute all technical indicators for an index.

    Args:
        historical_df: DataFrame with Date index and 'Close' column.

    Returns:
        Dict with:
            - price: latest closing price
            - sma20, sma50, sma100: latest SMA values
            - rsi14: latest RSI(14) value
            - above_sma20, above_sma50, above_sma100: bool flags
            - below_sma20, below_sma50, below_sma100: bool flags
            - rsi_label: str ("Overbought", "Oversold", "Neutral", etc.)
    """
    if historical_df.empty or "Close" not in historical_df.columns:
        return {
            "price": 0.0,
            "sma20": 0.0,
            "sma50": 0.0,
            "sma100": 0.0,
            "rsi14": 50.0,
            "above_sma20": False,
            "above_sma50": False,
            "above_sma100": False,
            "below_sma20": False,
            "below_sma50": False,
            "below_sma100": False,
            "rsi_label": "N/A",
        }

    closes = historical_df["Close"]

    sma20 = compute_sma(closes, 20)
    sma50 = compute_sma(closes, 50)
    sma100 = compute_sma(closes, 100)
    rsi = compute_rsi(closes, 14)

    latest_price = float(closes.iloc[-1])
    latest_sma20 = float(sma20.iloc[-1]) if pd.notna(sma20.iloc[-1]) else 0.0
    latest_sma50 = float(sma50.iloc[-1]) if pd.notna(sma50.iloc[-1]) else 0.0
    latest_sma100 = float(sma100.iloc[-1]) if pd.notna(sma100.iloc[-1]) else 0.0
    latest_rsi = float(rsi.iloc[-1]) if pd.notna(rsi.iloc[-1]) else 50.0

    if latest_rsi >= 70:
        rsi_label = "Overbought"
    elif latest_rsi <= 30:
        rsi_label = "Oversold"
    elif 40 <= latest_rsi <= 60:
        rsi_label = "Neutral"
    elif latest_rsi > 60:
        rsi_label = "Bullish"
    else:
        rsi_label = "Bearish"

    return {
        "price": round(latest_price, 2),
        "sma20": round(latest_sma20, 2),
        "sma50": round(latest_sma50, 2),
        "sma100": round(latest_sma100, 2),
        "rsi14": round(latest_rsi, 2),
        "above_sma20": latest_price > latest_sma20,
        "above_sma50": latest_price > latest_sma50,
        "above_sma100": latest_price > latest_sma100,
        "below_sma20": latest_price < latest_sma20,
        "below_sma50": latest_price < latest_sma50,
        "below_sma100": latest_price < latest_sma100,
        "rsi_label": rsi_label,
    }
