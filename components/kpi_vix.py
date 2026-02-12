"""
KPI Card 1: VIX Regime – Volatility Traffic Light.

Displays the current VIX level, daily change, and a color-coded
status indicator showing whether the current volatility
environment favors premium selling.
"""

from dash import html

_ACCENT_COLOR_MAP = {
    "green": "accent-green",
    "yellow": "accent-yellow",
    "red": "accent-red",
    "slate": "accent-slate",
}

_ICON_COLOR_MAP = {
    "green": "icon-green",
    "yellow": "icon-yellow",
    "red": "icon-red",
    "slate": "icon-slate",
}

_BADGE_COLOR_MAP = {
    "green": "badge-green",
    "yellow": "badge-yellow",
    "red": "badge-red",
    "slate": "badge-slate",
}


def create_vix_card() -> html.Div:
    """Create an empty VIX Regime KPI card with slate styling (accent, icon, badge)."""
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
                        className="kpi-badge badge-slate",
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
    Update the VIX Regime KPI card display values and styling.

    Color progression: slate (default) → green (favorable) → yellow (caution) → red (risk).
    Accent bar, icon, and badge are all set to the same regime color via CSS classes.

    Returns:
        (vix_value_text, vix_change_text, vix_badge_text,
        vix_accent_class_name, vix_icon_class_name, vix_badge_class_name)
    """
    color = traffic_light.get("color", "slate")
    label = traffic_light.get("label", "N/A")

    change_text = f"{vix_change:+.1f} ({vix_change_pct:+.1f}%) today"

    vix_accent_class_name = f"kpi-accent {_ACCENT_COLOR_MAP.get(color, 'accent-slate')}"
    vix_icon_class_name = f"bi bi-graph-up-arrow kpi-icon {_ICON_COLOR_MAP.get(color, 'icon-slate')}"
    vix_badge_class_name = f"kpi-badge {_BADGE_COLOR_MAP.get(color, 'badge-slate')}"

    return (
        f"{vix_level:.1f}",
        change_text,
        label,
        vix_accent_class_name,
        vix_icon_class_name,
        vix_badge_class_name,
    )
