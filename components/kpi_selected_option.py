"""
KPI Card 5: Selected Option Performance.

Displays details for a specific option contract selected from the chain table.
Initially empty; populated when a row is clicked in the option chain.
"""

import dash_bootstrap_components as dbc
from dash import html

_COLOR_MAP = {
    "green": "success",
    "yellow": "warning",
    "red": "danger",
}

_BORDER_MAP = {
    "green": "border-start border-success border-4",
    "yellow": "border-start border-warning border-4",
    "red": "border-start border-danger border-4",
}


def create_selected_option_card() -> dbc.Card:
    """Create the initial (empty) Selected Option Performance card."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    "Selected Option",
                    className="card-title text-muted mb-1",
                ),
                html.H3(
                    "Click a row in the chain",
                    id="selected-option-value",
                    className="mb-1 fs-6 text-muted",
                ),
                html.P(
                    "",
                    id="selected-option-detail",
                    className="small mb-1",
                ),
                html.P(
                    "",
                    id="selected-option-liquidity",
                    className="small mb-2",
                ),
                dbc.Badge(
                    "",
                    id="selected-option-badge",
                    color="secondary",
                    className="px-3 py-2",
                    style={"display": "none"},
                ),
            ]
        ),
        id="selected-option-card",
        className="h-100 shadow-sm",
    )


def update_selected_option_card(
    option_data: dict,
    performance_color: dict,
    strategy_label: str,
) -> tuple:
    """
    Return updated values for the Selected Option Performance card.

    Args:
        option_data: Dict with option details (from the chain row).
        performance_color: Dict from selected_option_color().
        strategy_label: "Short Call" or "Cash-Secured Put".

    Returns:
        (value_text, detail_text, liquidity_text, badge_text, badge_color,
         badge_style, card_class)
    """
    ann_return = option_data.get("ann_return", 0)
    color = performance_color.get("color", "yellow")
    label = performance_color.get("label", "")

    strike = option_data.get("strike", 0)
    expiration = option_data.get("expiration", "")
    dte = option_data.get("dte", 0)
    delta = option_data.get("delta", "N/A")
    iv = option_data.get("impliedVolatility", 0)
    oi = option_data.get("openInterest", 0)
    volume = option_data.get("volume", 0)
    symbol = option_data.get("contractSymbol", "")

    # Format IV as percentage
    iv_pct = iv * 100 if iv and iv < 1 else (iv if iv else 0)

    value_text = f"Ann. Return: {ann_return:.1f}% ({color.capitalize()})"

    # Format delta display
    if delta is not None and delta != "N/A":
        delta_str = f"\u0394 {delta:.2f}"
    else:
        delta_str = "\u0394 N/A"

    detail_text = (
        f"{strategy_label} | {symbol} | "
        f"{dte} DTE | {delta_str} | IV {iv_pct:.0f}%"
    )
    liquidity_text = f"OI {oi:,} | Vol {volume:,}"

    badge_variant = _COLOR_MAP.get(color, "secondary")
    border_class = _BORDER_MAP.get(color, "")

    return (
        value_text,
        detail_text,
        liquidity_text,
        f"{color.capitalize()} \u2013 {label}",
        badge_variant,
        {"display": "inline-block"},
        f"h-100 shadow-sm {border_class}",
    )
