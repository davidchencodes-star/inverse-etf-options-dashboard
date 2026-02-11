"""
Traffic-light logic for all dashboard indicators.

Centralizes all color assignment rules from the spec:
- VIX regime (Table 2)
- S&P 500 / Nasdaq technical regime (Tables 3 & 4)
- Per-option traffic light (Table 7)
- ETF status summary (KPI Card 4)
- Selected option performance (Table 5)
"""

from typing import Any

import pandas as pd


# =========================================================================
# VIX Regime Traffic Light (KPI Card 1, Spec Table 2)
# =========================================================================


def vix_traffic_light(vix_level: float, config: dict) -> dict[str, str]:
    """
    Determine VIX regime color.

    Args:
        vix_level: Current VIX value.
        config: Full config dict.

    Returns:
        {"color": "green"|"yellow"|"red", "label": str}
    """
    vix_cfg = config.get("vix_regime", {})
    green_range = vix_cfg.get("green", [18, 28])
    red_threshold = vix_cfg.get("red", 35)

    if green_range[0] <= vix_level <= green_range[1]:
        return {
            "color": "green",
            "label": "Favorable for premium selling",
        }
    elif vix_level >= red_threshold:
        return {
            "color": "red",
            "label": "Extreme stress \u2013 consider reducing size or pausing",
        }
    else:
        # Yellow: <18 or 28-35
        if vix_level < green_range[0]:
            return {
                "color": "yellow",
                "label": "Low volatility \u2013 thin premiums",
            }
        else:
            return {
                "color": "yellow",
                "label": "Elevated risk \u2013 proceed with caution",
            }


# =========================================================================
# Index Technical Regime Traffic Light (KPI Cards 2 & 3, Spec Tables 3 & 4)
# =========================================================================


def index_traffic_light(
    technicals: dict[str, Any],
    strategy: str,
    config: dict,
) -> dict[str, str]:
    """
    Determine index (S&P 500 or Nasdaq) technical regime color.

    Color changes based on the selected strategy (short_calls or cash_secured_puts).

    Args:
        technicals: Dict from calculations.technicals.get_index_technicals().
        strategy: "short_calls" or "cash_secured_puts".
        config: Full config dict.

    Returns:
        {"color": "green"|"yellow"|"red", "label": str}
    """
    rsi_cfg = config.get("rsi_thresholds", {})
    overbought = rsi_cfg.get("overbought", 70)
    oversold = rsi_cfg.get("oversold", 30)
    neutral_low = rsi_cfg.get("neutral_low", 40)
    neutral_high = rsi_cfg.get("neutral_high", 60)

    above_sma20 = technicals.get("above_sma20", False)
    above_sma50 = technicals.get("above_sma50", False)
    above_sma100 = technicals.get("above_sma100", False)
    rsi = technicals.get("rsi14", 50.0)
    sma20 = technicals.get("sma20", 0)
    sma50 = technicals.get("sma50", 0)

    if strategy == "short_calls":
        # ----- Short Calls (bearish/neutral bias) -----
        # Green: Downtrend or weakening + RSI >= 60 (overbought, rally exhausted)
        downtrend_or_weakening = (
            (not above_sma20 and not above_sma50)
            or (sma20 < sma50 and sma20 > 0 and sma50 > 0)
        )
        if downtrend_or_weakening and rsi >= neutral_high:
            return {
                "color": "green",
                "label": "Favorable for Short Calls \u2013 weakening trend + overbought",
            }

        # Red: Strong uptrend + RSI < 60 (trend still building)
        strong_uptrend = above_sma20 and above_sma50 and above_sma100
        if strong_uptrend and rsi < neutral_high:
            return {
                "color": "red",
                "label": "Avoid Short Calls \u2013 strong uptrend still building",
            }

        # Yellow: everything else (mixed trend and/or RSI 40-60)
        return {
            "color": "yellow",
            "label": "Mixed signals for Short Calls \u2013 proceed with caution",
        }

    else:
        # ----- Cash-Secured Puts (bullish/neutral bias) -----
        # Green: Uptrend + RSI <= 40 (pullback within uptrend)
        strong_uptrend = above_sma20 and above_sma50 and above_sma100
        if strong_uptrend and rsi <= neutral_low:
            return {
                "color": "green",
                "label": "Favorable for CSP \u2013 uptrend with pullback",
            }

        # Red: Strong downtrend + RSI < 40 (falling knife)
        strong_downtrend = not above_sma50 and not above_sma100
        if strong_downtrend and rsi < neutral_low:
            return {
                "color": "red",
                "label": "Avoid CSP \u2013 falling knife risk",
            }

        # Yellow: mixed trend or RSI 40-60
        return {
            "color": "yellow",
            "label": "Mixed signals for CSP \u2013 proceed with caution",
        }


# =========================================================================
# Per-Option Traffic Light (Option Chain, Spec Table 7)
# =========================================================================


def option_traffic_light(
    option_row: dict | pd.Series,
    vix_color: str,
    index_color: str,
    config: dict,
) -> dict[str, str]:
    """
    Determine the traffic-light color for a single option contract.

    Evaluates 5 boolean flags:
        1. return_ok: annualized return >= target
        2. delta_ok: delta within allowed band
        3. liquidity_ok: OI >= min and volume >= min
        4. vix_ok: VIX not in red regime
        5. index_ok: Index technical not red for selected strategy

    Args:
        option_row: Dict or Series with return_ok, delta_ok, liquidity_ok,
                    openInterest, volume, ann_return.
        vix_color: "green", "yellow", or "red" (from vix_traffic_light).
        index_color: "green", "yellow", or "red" (from index_traffic_light).
        config: Full config dict.

    Returns:
        {"color": "green"|"yellow"|"red", "tooltip": str}
    """
    return_ok = bool(option_row.get("return_ok", False))
    delta_ok = bool(option_row.get("delta_ok", False))
    liquidity_ok = bool(option_row.get("liquidity_ok", False))
    liquidity_marginal = bool(option_row.get("liquidity_marginal", False))

    vix_ok = vix_color != "red"
    index_ok = index_color in ("green", "yellow")

    oi = option_row.get("openInterest", 0) or 0
    volume = option_row.get("volume", 0) or 0
    ann_return = option_row.get("ann_return", 0) or 0
    marginal_oi = config.get("liquidity", {}).get("marginal_oi", 50)

    # --- RED conditions ---
    # Return too low, delta outside band, very low liquidity,
    # or both VIX red AND index red
    if not return_ok:
        return {
            "color": "red",
            "tooltip": f"Annualized return {ann_return:.1f}% below target",
        }
    if not delta_ok:
        delta_val = option_row.get("delta", "N/A")
        return {
            "color": "red",
            "tooltip": f"Delta {delta_val} outside allowed band",
        }
    if oi < marginal_oi or volume == 0:
        return {
            "color": "red",
            "tooltip": f"Very low liquidity (OI={oi}, Vol={volume})",
        }
    if vix_color == "red" and index_color == "red":
        return {
            "color": "red",
            "tooltip": "High-risk environment \u2013 VIX and index both red",
        }

    # --- GREEN conditions ---
    # All 5 flags pass
    if return_ok and delta_ok and liquidity_ok and vix_ok and index_ok:
        return {
            "color": "green",
            "tooltip": (
                f"\u2713 {ann_return:.1f}% annualized, delta in band, "
                f"liquidity OK, VIX & index regime supportive"
            ),
        }

    # --- YELLOW: return_ok and delta_ok, but something else is marginal ---
    issues = []
    if not liquidity_ok:
        issues.append(f"Marginal liquidity (OI={oi}, Vol={volume})")
    if vix_color == "yellow":
        issues.append("VIX in yellow zone")
    if vix_color == "red":
        issues.append("VIX in red zone")
    if index_color in ("yellow", "red"):
        issues.append(f"Index technical is {index_color}")

    tooltip = "; ".join(issues) if issues else "Near threshold"
    return {"color": "yellow", "tooltip": tooltip}


# =========================================================================
# Selected Option Performance Color (KPI Card 5, Spec Table 5)
# =========================================================================


def selected_option_color(
    ann_return: float,
    oi: int,
    volume: int,
    config: dict,
) -> dict[str, str]:
    """
    Determine color for the Selected Option Performance card.

    Args:
        ann_return: Annualized return percentage.
        oi: Open interest.
        volume: Daily volume.
        config: Full config dict.

    Returns:
        {"color": "green"|"yellow"|"red", "label": str}
    """
    target = config.get("annualized_return_target", 30)
    min_oi = config.get("liquidity", {}).get("min_oi", 200)
    min_vol = config.get("liquidity", {}).get("min_volume", 20)
    marginal_oi = config.get("liquidity", {}).get("marginal_oi", 50)

    liquidity_ok = oi >= min_oi and volume >= min_vol
    liquidity_poor = oi < marginal_oi or volume == 0

    if ann_return >= target and liquidity_ok:
        return {"color": "green", "label": "Meets all targets"}
    elif ann_return < 20 or liquidity_poor:
        return {"color": "red", "label": "Below minimum thresholds"}
    else:
        return {"color": "yellow", "label": "Near threshold \u2013 review carefully"}


# =========================================================================
# ETF Status Summary (KPI Card 4)
# =========================================================================


def etf_status_summary(
    chains: dict[str, dict[str, pd.DataFrame]],
    underlying_prices: dict[str, float],
    vix_color: str,
    sp_color: str,
    ndx_color: str,
    strategy: str,
    config: dict,
) -> list[dict[str, Any]]:
    """
    Compute summary status for each inverse ETF.

    Args:
        chains: {etf: {exp_date_str: enriched_chain_df}}
        underlying_prices: {etf: float}
        vix_color: VIX regime color.
        sp_color: S&P 500 regime color.
        ndx_color: Nasdaq regime color.
        strategy: "short_calls" or "cash_secured_puts".
        config: Full config dict.

    Returns:
        List of dicts, one per ETF:
        {
            "symbol": str,
            "last_price": float,
            "green_calls": int,
            "green_puts": int,
            "total_green": int,
            "status_color": "green"|"yellow"|"red",
        }
    """
    etfs = config.get("etfs", [])
    results = []

    for etf in etfs:
        etf_chains = chains.get(etf, {})
        last_price = underlying_prices.get(etf, 0.0)

        green_calls = 0
        green_puts = 0
        yellow_count = 0

        # Determine which index color to use for this ETF
        # SQQQ uses Nasdaq, others use S&P
        idx_color = ndx_color if etf == "SQQQ" else sp_color

        for _exp_key, chain_df in etf_chains.items():
            if chain_df.empty:
                continue

            for _, row in chain_df.iterrows():
                tl = option_traffic_light(row, vix_color, idx_color, config)
                if tl["color"] == "green":
                    if row.get("type") == "call":
                        green_calls += 1
                    else:
                        green_puts += 1
                elif tl["color"] == "yellow":
                    yellow_count += 1

        total_green = green_calls + green_puts

        # Overall ETF status
        if total_green >= 1:
            status_color = "green"
        elif yellow_count > 0:
            status_color = "yellow"
        else:
            status_color = "red"

        results.append(
            {
                "symbol": etf,
                "last_price": round(last_price, 2),
                "green_calls": green_calls,
                "green_puts": green_puts,
                "total_green": total_green,
                "status_color": status_color,
            }
        )

    return results
