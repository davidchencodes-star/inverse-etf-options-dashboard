"""
High-level data orchestrator.

Coordinates data fetching from the configured provider, applies caching,
computes Greeks when needed, and returns a unified market data dict
for the calculation layer.
"""

import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from data import cache
from data.greeks import compute_greeks_for_chain
from data.provider import DataProvider
from data.yfinance_provider import YFinanceProvider

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


def _load_config() -> dict:
    """Load configuration from config.yaml."""
    with open(_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def _get_provider(config: dict) -> DataProvider:
    """Instantiate the configured data provider."""
    provider_name = config.get("data_provider", "yfinance")
    if provider_name == "yfinance":
        return YFinanceProvider()
    # Future: elif provider_name == "tradier": return TradierProvider(...)
    raise ValueError(f"Unknown data provider: {provider_name}")


# ---------------------------------------------------------------------------
# Expiration date selection
# ---------------------------------------------------------------------------


def _find_nearest_expiration(
    expirations: list[date], target_dte: int
) -> date | None:
    """
    Find the expiration date closest to a target DTE.

    Skips expirations that are already past. Prefers the nearest future
    expiration to the target.
    """
    today = date.today()
    future_exps = [e for e in expirations if e > today]

    if not future_exps:
        return None

    target_date = today + timedelta(days=target_dte)
    return min(future_exps, key=lambda e: abs((e - target_date).days))


# ---------------------------------------------------------------------------
# Core data fetching
# ---------------------------------------------------------------------------

# Module-level state
_last_error: str | None = None
_provider_instance: DataProvider | None = None
_config_cache: dict | None = None


def get_config() -> dict:
    """Get the cached config, loading once on first call."""
    global _config_cache
    if _config_cache is None:
        _config_cache = _load_config()
    return _config_cache


def reload_config() -> dict:
    """Force-reload config from disk."""
    global _config_cache
    _config_cache = _load_config()
    return _config_cache


def _get_or_create_provider() -> DataProvider:
    """Get or create the data provider singleton."""
    global _provider_instance
    if _provider_instance is None:
        config = get_config()
        _provider_instance = _get_provider(config)
    return _provider_instance


def get_last_error() -> str | None:
    """Return the last error message from data fetching, if any."""
    return _last_error


def refresh_all() -> dict[str, Any]:
    """
    Fetch all market data in one pass and update the cache.

    Returns a unified dict with all data needed by the dashboard:
    {
        "quotes": {symbol: {last, bid, ask, volume, change, change_pct, prev_close}},
        "chains": {symbol: {expiration_date: DataFrame}},
        "historical": {symbol: DataFrame},
        "expirations": {symbol: {target_dte: actual_expiration_date}},
        "stale_warning": bool,
        "last_refresh": datetime,
    }
    """
    global _last_error
    _last_error = None

    config = get_config()
    provider = _get_or_create_provider()
    ttl = config.get("refresh_interval_minutes", 5) * 60
    risk_free_rate = config.get("risk_free_rate", 0.05)

    etfs = config.get("etfs", [])
    index_proxies = config.get("index_proxies", {})
    vix_symbol = config.get("vix_symbol", "^VIX")
    target_dtes = config.get("expirations_dte", [7, 14])
    hist_days = config.get("historical_days", 150)

    # All symbols we need quotes for
    all_quote_symbols = (
        etfs
        + list(index_proxies.values())
        + [vix_symbol]
    )

    # --- Fetch quotes ---
    stale = False
    quotes = cache.get("quotes")
    if quotes is None:
        try:
            quotes = provider.get_quotes(all_quote_symbols)
            cache.set("quotes", quotes, ttl_seconds=ttl)
        except Exception as e:
            logger.error("Failed to fetch quotes: %s", e)
            _last_error = f"Quote fetch failed: {e}"
            quotes = cache.get("quotes") or {}
            stale = True

    # --- Fetch historical for index proxies (for SMA/RSI) ---
    historical: dict[str, pd.DataFrame] = {}
    for name, symbol in index_proxies.items():
        cache_key = f"historical_{symbol}"
        cached = cache.get(cache_key)
        if cached is not None:
            historical[symbol] = cached
        else:
            try:
                df = provider.get_historical(symbol, days=hist_days)
                if not df.empty:
                    cache.save_historical(symbol, df)
                    cache.set(cache_key, df, ttl_seconds=ttl)
                    historical[symbol] = df
                else:
                    # Try loading from SQLite fallback
                    df = cache.load_historical(symbol, days=hist_days)
                    historical[symbol] = df
                    if df.empty:
                        stale = True
            except Exception as e:
                logger.error("Failed to fetch historical for %s: %s", symbol, e)
                _last_error = f"Historical fetch failed for {symbol}: {e}"
                df = cache.load_historical(symbol, days=hist_days)
                historical[symbol] = df
                stale = True

    # --- Fetch option expirations and chains ---
    expirations_map: dict[str, dict[int, date]] = {}
    chains: dict[str, dict[str, pd.DataFrame]] = {}

    for etf in etfs:
        # Get expirations
        exp_cache_key = f"expirations_{etf}"
        expirations = cache.get(exp_cache_key)
        if expirations is None:
            try:
                expirations = provider.get_option_expirations(etf)
                cache.set(exp_cache_key, expirations, ttl_seconds=ttl)
            except Exception as e:
                logger.error("Failed to fetch expirations for %s: %s", etf, e)
                expirations = []
                stale = True

        # Find nearest expiration for each target DTE
        etf_exps: dict[int, date] = {}
        etf_chains: dict[str, pd.DataFrame] = {}

        for target_dte in target_dtes:
            nearest = _find_nearest_expiration(expirations, target_dte)
            if nearest is None:
                continue
            etf_exps[target_dte] = nearest

            # Fetch chain
            chain_cache_key = f"chain_{etf}_{nearest}"
            chain_df = cache.get(chain_cache_key)
            if chain_df is None:
                try:
                    chain_df = provider.get_option_chain(etf, nearest)
                    if not chain_df.empty:
                        # Get underlying price for Greeks computation
                        etf_quote = quotes.get(etf, {})
                        underlying_price = etf_quote.get("last", 0)

                        if underlying_price > 0 and "delta" not in chain_df.columns:
                            chain_df = compute_greeks_for_chain(
                                chain_df,
                                underlying_price=underlying_price,
                                risk_free_rate=risk_free_rate,
                            )

                        cache.set(chain_cache_key, chain_df, ttl_seconds=ttl)
                except Exception as e:
                    logger.error(
                        "Failed to fetch chain for %s exp %s: %s",
                        etf,
                        nearest,
                        e,
                    )
                    _last_error = f"Chain fetch failed for {etf}: {e}"
                    chain_df = pd.DataFrame()
                    stale = True

            if chain_df is not None and not chain_df.empty:
                etf_chains[str(nearest)] = chain_df

        expirations_map[etf] = etf_exps
        chains[etf] = etf_chains

    result = {
        "quotes": quotes,
        "chains": chains,
        "historical": historical,
        "expirations": expirations_map,
        "stale_warning": stale,
        "last_refresh": datetime.now(),
    }

    # Cache the full result for quick access
    cache.set("market_data", result, ttl_seconds=ttl)

    return result


def get_market_data() -> dict[str, Any]:
    """
    Get current market data (from cache if fresh, else triggers refresh).

    Returns the same structure as refresh_all().
    """
    cached = cache.get("market_data")
    if cached is not None:
        return cached
    return refresh_all()
