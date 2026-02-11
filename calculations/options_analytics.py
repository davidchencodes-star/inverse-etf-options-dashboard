"""
Options analytics calculations.

Computes annualized return, IV rank, payoff tables, and enriches
option chain DataFrames with computed columns and boolean flags.
"""

import numpy as np
import pandas as pd


def annualized_return(premium: float, underlying_price: float, dte: int) -> float:
    """
    Compute annualized return for a short option position.

    Formula: (premium / underlying_price) * (365 / DTE) * 100

    Args:
        premium: Option mid-price (premium collected).
        underlying_price: Current underlying price.
        dte: Days to expiration (calendar days).

    Returns:
        Annualized return as a percentage. Returns 0.0 if inputs are invalid.
    """
    if underlying_price <= 0 or dte <= 0 or premium <= 0:
        return 0.0
    return round((premium / underlying_price) * (365.0 / dte) * 100.0, 2)


def iv_rank(current_iv: float, iv_52w_high: float, iv_52w_low: float) -> float:
    """
    Compute IV rank (percentile of current IV within 52-week range).

    Formula: (current_iv - iv_low) / (iv_high - iv_low) * 100

    Returns:
        IV rank as percentage (0-100). Returns 0.0 if range is zero.
    """
    if iv_52w_high <= iv_52w_low or iv_52w_high == 0:
        return 0.0
    return round(
        (current_iv - iv_52w_low) / (iv_52w_high - iv_52w_low) * 100.0, 1
    )


def compute_payoff_table(
    option_type: str,
    strike: float,
    premium: float,
    underlying_price: float,
    num_points: int = 50,
) -> pd.DataFrame:
    """
    Generate a P/L payoff table at expiration for a SHORT option.

    Args:
        option_type: 'call' or 'put'.
        strike: Strike price.
        premium: Premium received (mid-price).
        underlying_price: Current underlying price (for range centering).
        num_points: Number of price points to compute.

    Returns:
        DataFrame with columns: underlying_at_expiry, pnl, breakeven.
    """
    # Price range: +/- 30% around current price
    price_low = underlying_price * 0.70
    price_high = underlying_price * 1.30
    prices = np.linspace(price_low, price_high, num_points)

    pnl = []
    for price in prices:
        if option_type == "call":
            # Short call: profit = premium - max(0, price - strike)
            intrinsic = max(0, price - strike)
            pnl.append(premium - intrinsic)
        else:
            # Short put: profit = premium - max(0, strike - price)
            intrinsic = max(0, strike - price)
            pnl.append(premium - intrinsic)

    # Breakeven
    if option_type == "call":
        breakeven = strike + premium
    else:
        breakeven = strike - premium

    df = pd.DataFrame(
        {
            "underlying_at_expiry": np.round(prices, 2),
            "pnl": np.round(pnl, 2),
        }
    )

    return df, round(breakeven, 2)


def enrich_chain(
    chain_df: pd.DataFrame,
    underlying_price: float,
    config: dict,
) -> pd.DataFrame:
    """
    Enrich an option chain DataFrame with computed analytics and flags.

    Adds columns:
        - mid: (bid + ask) / 2
        - ann_return: annualized return %
        - return_ok: bool (ann_return >= target)
        - delta_ok: bool (delta within allowed band for option type)
        - delta_in_focus: bool (delta within focus band)
        - liquidity_ok: bool (OI >= min and volume >= min)
        - liquidity_marginal: bool (OI < min but >= marginal)

    Args:
        chain_df: Option chain DataFrame with standard columns.
        underlying_price: Current underlying price.
        config: Configuration dict from config.yaml.

    Returns:
        Enriched DataFrame.
    """
    if chain_df.empty:
        return chain_df

    df = chain_df.copy()

    # --- Mid-price ---
    df["mid"] = ((df["bid"] + df["ask"]) / 2).round(4)

    # --- Annualized return ---
    dte_col = "dte" if "dte" in df.columns else "DTE"
    df["ann_return"] = df.apply(
        lambda row: annualized_return(
            premium=row["mid"],
            underlying_price=underlying_price,
            dte=row[dte_col],
        ),
        axis=1,
    )

    # --- Config thresholds ---
    return_target = config.get("annualized_return_target", 30)
    delta_bands = config.get("delta_bands", {})
    liquidity_cfg = config.get("liquidity", {})

    call_band = delta_bands.get("short_calls", [0.10, 0.50])
    call_focus = delta_bands.get("short_calls_focus", [0.20, 0.30])
    put_band = delta_bands.get("short_puts", [-0.50, -0.10])
    put_focus = delta_bands.get("short_puts_focus", [-0.30, -0.20])

    min_oi = liquidity_cfg.get("min_oi", 200)
    min_volume = liquidity_cfg.get("min_volume", 20)
    marginal_oi = liquidity_cfg.get("marginal_oi", 50)

    # --- Return flag ---
    df["return_ok"] = df["ann_return"] >= return_target

    # --- Delta flags ---
    def check_delta_ok(row):
        delta = row.get("delta")
        if delta is None or pd.isna(delta):
            return False
        if row["type"] == "call":
            return call_band[0] <= delta <= call_band[1]
        else:
            return put_band[0] <= delta <= put_band[1]

    def check_delta_focus(row):
        delta = row.get("delta")
        if delta is None or pd.isna(delta):
            return False
        if row["type"] == "call":
            return call_focus[0] <= delta <= call_focus[1]
        else:
            return put_focus[0] <= delta <= put_focus[1]

    df["delta_ok"] = df.apply(check_delta_ok, axis=1)
    df["delta_in_focus"] = df.apply(check_delta_focus, axis=1)

    # --- Liquidity flags ---
    df["liquidity_ok"] = (df["openInterest"] >= min_oi) & (
        df["volume"] >= min_volume
    )
    df["liquidity_marginal"] = (
        (df["openInterest"] < min_oi) & (df["openInterest"] >= marginal_oi)
    ) | ((df["volume"] < min_volume) & (df["volume"] > 0))

    return df
