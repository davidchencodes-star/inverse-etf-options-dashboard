"""
Abstract data provider interface.

Swap providers by changing `data_provider` in config.yaml.
All providers must implement this interface.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Any

import pandas as pd


class DataProvider(ABC):
    """Base class for all market data providers."""

    @abstractmethod
    def get_quotes(self, symbols: list[str]) -> dict[str, dict[str, Any]]:
        """
        Fetch current quotes for a list of symbols.

        Returns dict keyed by symbol, each value containing:
            - last: float (last traded price)
            - bid: float
            - ask: float
            - volume: int (daily volume)
            - change: float (daily point change)
            - change_pct: float (daily percent change)
            - prev_close: float
        """
        ...

    @abstractmethod
    def get_option_expirations(self, symbol: str) -> list[date]:
        """
        Get available option expiration dates for a symbol.

        Returns list of date objects sorted ascending.
        """
        ...

    @abstractmethod
    def get_option_chain(self, symbol: str, expiration: date) -> pd.DataFrame:
        """
        Fetch the full option chain for a symbol at a given expiration.

        Returns DataFrame with columns:
            - contractSymbol: str
            - type: str ('call' or 'put')
            - expiration: date
            - strike: float
            - bid: float
            - ask: float
            - last: float
            - volume: int
            - openInterest: int
            - impliedVolatility: float (as decimal, e.g. 0.65 = 65%)

        Greeks (delta, gamma, theta, vega) may or may not be included
        depending on the provider. If not, the fetch layer computes them.
        """
        ...

    @abstractmethod
    def get_historical(
        self, symbol: str, days: int = 150
    ) -> pd.DataFrame:
        """
        Fetch daily historical OHLCV data.

        Args:
            symbol: Ticker symbol.
            days: Number of calendar days of history to fetch.

        Returns DataFrame with columns:
            - Date (index, datetime)
            - Open, High, Low, Close, Volume
        """
        ...
