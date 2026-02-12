"""
VIX Regime Card - Volatility Traffic Light

Shows current VIX level, daily change, and color-coded regime indicator for
assessing premium selling opportunities.
"""

from dash import html


def create_vix_card() -> html.Div:
    """Create VIX Regime KPI card with default slate styling."""
    return html.Div(
        [
            html.Div("", id="vix-accent", className="kpi-accent accent-slate"),
            html.Div(
                [
                    html.P(
                        [
                            html.I(
                                id="vix-icon",
                                className="bi bi-graph-up-arrow kpi-icon icon-slate",
                            ),
                            "VIX Regime",
                        ],
                        className="kpi-title",
                    )
                ],
                className="kpi-header",
            ),
            html.Div(
                [
                    html.P("--", id="vix-value", className="kpi-value"),
                    html.P("--", id="vix-change", className="kpi-change"),
                    html.Br(),
                    html.Span(
                        "Loading...",
                        id="vix-badge",
                        className="mt-2 kpi-badge badge-slate",
                    ),
                ],
                className="kpi-body",
            ),
        ],
        id="kpi-card-vix",
        className="kpi-card",
    )


def update_vix_card(
    vix_level: float,
    vix_change: float,
    vix_change_pct: float,
    traffic_light: dict,
) -> tuple:
    """
    Update VIX card values and colors based on current volatility regime.
    
    Args:
        vix_level: Current VIX value
        vix_change: Daily point change
        vix_change_pct: Daily percentage change
        traffic_light: Dict with 'color' and 'label' keys
    
    Returns:
        Tuple of 6 strings for updating card components:
        (value, change_text, badge_text, accent_class, icon_class, badge_class)
    """
    color = traffic_light.get("color", "slate")
    label = traffic_light.get("label", "N/A")

    if (color not in ["green", "yellow", "red", "slate"]):
        color = "slate"
    
    return (
        f"{vix_level:.1f}",
        f"{vix_change:+.1f} ({vix_change_pct:+.1f}%) today",
        label,
        f"kpi-accent accent-{color}",
        f"bi bi-graph-up-arrow kpi-icon icon-{color}",
        f"mt-2 kpi-badge badge-{color}",
    )
