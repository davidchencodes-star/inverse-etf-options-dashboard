"""
KPI Card 1: VIX Regime -- Volatility Traffic Light.

Displays current VIX level, daily change, and a colored status pill
indicating whether the volatility environment favors premium selling.
"""

import dash_bootstrap_components as dbc
from dash import html

# Color mapping for Bootstrap badge variants
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


def create_vix_card() -> dbc.Card:
    """Create the initial (empty) VIX Regime KPI card."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6("VIX Regime", className="card-title text-muted mb-1"),
                html.H3("--", id="vix-value", className="mb-1"),
                html.P("--", id="vix-change", className="text-muted small mb-2"),
                dbc.Badge(
                    "Loading...",
                    id="vix-badge",
                    color="secondary",
                    className="px-3 py-2",
                ),
            ]
        ),
        id="vix-card",
        className="h-100 shadow-sm",
    )


def update_vix_card(
    vix_level: float,
    vix_change: float,
    vix_change_pct: float,
    traffic_light: dict,
) -> tuple:
    """
    Return updated values for VIX card components.

    Returns:
        (vix_value_text, vix_change_text, badge_text, badge_color, card_class)
    """
    color = traffic_light.get("color", "yellow")
    label = traffic_light.get("label", "")

    # Format change text
    sign = "+" if vix_change >= 0 else ""
    change_text = f"{sign}{vix_change:.1f} ({sign}{vix_change_pct:.1f}%) today"

    badge_variant = _COLOR_MAP.get(color, "secondary")
    border_class = _BORDER_MAP.get(color, "")

    return (
        f"{vix_level:.1f}",
        change_text,
        f"{color.capitalize()} \u2013 {label}",
        badge_variant,
        f"h-100 shadow-sm {border_class}",
    )
