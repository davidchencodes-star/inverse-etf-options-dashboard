"""
yfinance-based data provider.

No API key required. Provides 15-min delayed quotes, option chains
(with IV but without Greeks), and historical daily data.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any

import pandas as pd
import yfinance as yf

from data.provider import DataProvider

logger = logging.getLogger(__name__)


class YFinanceProvider(DataProvider):
    """Market data provider using the yfinance library (free, no API key)."""

    # ------------------------------------------------------------------ #
    #  Quotes
    # ------------------------------------------------------------------ #
    def get_quotes(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch current quotes for multiple symbols."""
        results: dict[str, dict[str, Any]] = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.fast_info

                # fast_info provides the essentials
                last_price = getattr(info, "last_price", None) or 0.0
                prev_close = getattr(info, "previous_close", None) or 0.0
                change = round(last_price - prev_close, 4) if prev_close else 0.0
                change_pct = (
                    round((change / prev_close) * 100, 2) if prev_close else 0.0
                )

                # Bid/ask may not always be available via fast_info
                # Fall back to full info if needed
                bid = getattr(info, "bid", None) or 0.0
                ask = getattr(info, "ask", None) or 0.0

                # If bid/ask are 0, try the full info dict
                if bid == 0 or ask == 0:
                    try:
                        full_info = ticker.info
                        bid = full_info.get("bid", 0.0) or 0.0
                        ask = full_info.get("ask", 0.0) or 0.0
                    except Exception:
                        pass

                results[symbol] = {
                    "last": round(last_price, 4),
                    "bid": round(bid, 4),
                    "ask": round(ask, 4),
                    "volume": int(getattr(info, "last_volume", 0) or 0),
                    "change": change,
                    "change_pct": change_pct,
                    "prev_close": round(prev_close, 4),
                }
            except Exception as e:
                logger.warning("Failed to fetch quote for %s: %s", symbol, e)
                results[symbol] = {
                    "last": 0.0,
                    "bid": 0.0,
                    "ask": 0.0,
                    "volume": 0,
                    "change": 0.0,
                    "change_pct": 0.0,
                    "prev_close": 0.0,
                }

        return results

    # ------------------------------------------------------------------ #
    #  Option Expirations
    # ------------------------------------------------------------------ #
    def get_option_expirations(self, symbol: str) -> list[date]:
        """Get available option expiration dates."""
        try:
            ticker = yf.Ticker(symbol)
            expirations = ticker.options  # tuple of date strings 'YYYY-MM-DD'
            return [
                datetime.strptime(exp, "%Y-%m-%d").date() for exp in expirations
            ]
        except Exception as e:
            logger.warning(
                "Failed to fetch expirations for %s: %s", symbol, e
            )
            return []

    # ------------------------------------------------------------------ #
    #  Option Chain
    # ------------------------------------------------------------------ #
    def get_option_chain(self, symbol: str, expiration: date) -> pd.DataFrame:
        """
        Fetch the option chain for a symbol at a given expiration.

        yfinance returns calls and puts as separate DataFrames.
        We combine them into a single DataFrame with a 'type' column.
        """
        try:
            ticker = yf.Ticker(symbol)
            exp_str = expiration.strftime("%Y-%m-%d")
            chain = ticker.option_chain(exp_str)

            calls = chain.calls.copy()
            calls["type"] = "call"

            puts = chain.puts.copy()
            puts["type"] = "put"

            combined = pd.concat([calls, puts], ignore_index=True)

            # Standardize column names
            rename_map = {
                "contractSymbol": "contractSymbol",
                "strike": "strike",
                "lastPrice": "last",
                "bid": "bid",
                "ask": "ask",
                "volume": "volume",
                "openInterest": "openInterest",
                "impliedVolatility": "impliedVolatility",
            }

            # Rename only columns that exist
            existing_renames = {
                k: v for k, v in rename_map.items() if k in combined.columns
            }
            combined = combined.rename(columns=existing_renames)

            # Add expiration and DTE
            combined["expiration"] = expiration
            today = date.today()
            combined["dte"] = (expiration - today).days

            # Ensure numeric types
            for col in ["strike", "last", "bid", "ask", "impliedVolatility"]:
                if col in combined.columns:
                    combined[col] = pd.to_numeric(combined[col], errors="coerce")

            for col in ["volume", "openInterest"]:
                if col in combined.columns:
                    combined[col] = (
                        pd.to_numeric(combined[col], errors="coerce")
                        .fillna(0)
                        .astype(int)
                    )

            # Select and order columns
            keep_cols = [
                "contractSymbol",
                "type",
                "expiration",
                "dte",
                "strike",
                "bid",
                "ask",
                "last",
                "volume",
                "openInterest",
                "impliedVolatility",
            ]
            keep_cols = [c for c in keep_cols if c in combined.columns]

            return combined[keep_cols].reset_index(drop=True)

        except Exception as e:
            logger.warning(
                "Failed to fetch option chain for %s exp %s: %s",
                symbol,
                expiration,
                e,
            )
            return pd.DataFrame()

    # ------------------------------------------------------------------ #
    #  Historical Data
    # ------------------------------------------------------------------ #
    def get_historical(self, symbol: str, days: int = 150) -> pd.DataFrame:
        """
        Fetch daily historical OHLCV data.

        Returns DataFrame indexed by Date with Open, High, Low, Close, Volume.
        """
        try:
            ticker = yf.Ticker(symbol)
            # Fetch enough data for SMA100 + buffer
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 30)

            df = ticker.history(
                start=start_date.strftime("%Y-%m-%d"),
                end=end_date.strftime("%Y-%m-%d"),
                interval="1d",
            )

            if df.empty:
                logger.warning("No historical data returned for %s", symbol)
                return pd.DataFrame()

            # Standardize: keep only OHLCV columns
            keep_cols = ["Open", "High", "Low", "Close", "Volume"]
            keep_cols = [c for c in keep_cols if c in df.columns]
            df = df[keep_cols]

            # Ensure the index is a proper DatetimeIndex
            df.index = pd.to_datetime(df.index)
            df.index.name = "Date"

            return df.tail(days)  # Return at most `days` rows

        except Exception as e:
            logger.warning(
                "Failed to fetch historical data for %s: %s", symbol, e
            )
            return pd.DataFrame()
