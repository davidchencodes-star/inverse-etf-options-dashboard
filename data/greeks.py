"""
Black-Scholes Greeks calculator.

Used when the data provider (e.g. yfinance) does not supply Greeks natively.
Computes delta, gamma, theta, and vega from underlying price, strike, time
to expiry, risk-free rate, and implied volatility.
"""

import math
from typing import Any

import numpy as np
from scipy.stats import norm


def _d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Compute d1 in the Black-Scholes formula."""
    return (math.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * math.sqrt(T))


def _d2(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Compute d2 in the Black-Scholes formula."""
    return _d1(S, K, T, r, sigma) - sigma * math.sqrt(T)


def compute_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str,
) -> dict[str, float | None]:
    """
    Compute Black-Scholes Greeks for a single option.

    Args:
        S: Current underlying price.
        K: Strike price.
        T: Time to expiration in years (DTE / 365).
        r: Risk-free interest rate (e.g. 0.05 for 5%).
        sigma: Implied volatility as decimal (e.g. 0.65 for 65%).
        option_type: 'call' or 'put'.

    Returns:
        Dict with keys: delta, gamma, theta, vega.
        Returns None values if inputs are invalid (T<=0, sigma<=0, etc.).
    """
    empty = {"delta": None, "gamma": None, "theta": None, "vega": None}

    # Guard against invalid inputs
    if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
        return empty

    try:
        d1 = _d1(S, K, T, r, sigma)
        d2 = _d2(S, K, T, r, sigma)
        sqrt_T = math.sqrt(T)

        # Gamma (same for calls and puts)
        gamma = norm.pdf(d1) / (S * sigma * sqrt_T)

        # Vega (same for calls and puts, per 1% move in IV)
        vega = S * norm.pdf(d1) * sqrt_T / 100.0

        if option_type == "call":
            delta = norm.cdf(d1)
            theta = (
                -(S * norm.pdf(d1) * sigma) / (2 * sqrt_T)
                - r * K * math.exp(-r * T) * norm.cdf(d2)
            ) / 365.0  # daily theta
        else:  # put
            delta = norm.cdf(d1) - 1.0
            theta = (
                -(S * norm.pdf(d1) * sigma) / (2 * sqrt_T)
                + r * K * math.exp(-r * T) * norm.cdf(-d2)
            ) / 365.0  # daily theta

        return {
            "delta": round(delta, 4),
            "gamma": round(gamma, 6),
            "theta": round(theta, 4),
            "vega": round(vega, 4),
        }
    except (ValueError, ZeroDivisionError, OverflowError):
        return empty


def compute_greeks_for_chain(
    chain_df: "pd.DataFrame",
    underlying_price: float,
    risk_free_rate: float = 0.05,
) -> "pd.DataFrame":
    """
    Add Greeks columns to an option chain DataFrame.

    Expects columns: strike, impliedVolatility, type, and either 'dte' or 'DTE'.
    Adds columns: delta, gamma, theta, vega.

    Args:
        chain_df: Option chain DataFrame.
        underlying_price: Current price of the underlying.
        risk_free_rate: Risk-free rate (default 0.05).

    Returns:
        DataFrame with Greeks columns added.
    """
    import pandas as pd

    df = chain_df.copy()

    # Determine DTE column name
    dte_col = "dte" if "dte" in df.columns else "DTE"

    greeks_data = []
    for _, row in df.iterrows():
        T = row[dte_col] / 365.0
        sigma = row.get("impliedVolatility", 0) or 0
        strike = row["strike"]
        opt_type = row["type"]

        greeks = compute_greeks(
            S=underlying_price,
            K=strike,
            T=T,
            r=risk_free_rate,
            sigma=sigma,
            option_type=opt_type,
        )
        greeks_data.append(greeks)

    greeks_df = pd.DataFrame(greeks_data)
    for col in ["delta", "gamma", "theta", "vega"]:
        df[col] = greeks_df[col].values

    return df
