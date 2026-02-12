"""
KPI Cards 2 & 3: S&P 500 / Nasdaq Technical Regime (SMA + RSI Traffic Light)

Shows the index price, SMA(20/50/100), and RSI(14), plus a color-coded status pill.
The pill color adapts to the selected strategy (Short Calls vs. Cash-Secured Puts).
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


def create_index_card(index_id: str, title: str) -> html.Div:
    """
    Create an Index Technical Regime KPI card.

    Args:
        index_id: Prefix for component IDs (e.g. "sp500" or "nasdaq").
        title: Card title (e.g. "S&P 500 Technical").
    """
    return html.Div(
        [
            html.Div("", id=f"{index_id}-accent", className="kpi-accent accent-slate"),
            html.Div(
                [
                    html.P(
                        [
                            html.I(
                                id=f"{index_id}-icon",
                                className="bi bi-bar-chart-line-fill kpi-icon icon-slate",
                            ),
                            title,
                        ],
                        className="kpi-title",
                    )
                ],
                className="kpi-header",
            ),
            html.Div(
                [
                    html.P("--", id=f"{index_id}-value", className="kpi-value"),
                    html.Div(
                        [
                            html.Span(
                                [
                                    "SMA20: ",
                                    html.Strong("--", id=f"{index_id}-sma20-value"),
                                ],
                                className="kpi-metric",
                            ),
                            html.Span(
                                [
                                    "SMA50: ",
                                    html.Strong("--", id=f"{index_id}-sma50-value"),
                                ],
                                className="kpi-metric",
                            ),
                            html.Span(
                                [
                                    "SMA100: ",
                                    html.Strong("--", id=f"{index_id}-sma100-value"),
                                ],
                                className="kpi-metric",
                            ),
                        ], 
                        className="kpi-metric-row"
                    ),
                    html.Div(
                        [
                            html.Span(
                                [
                                    "RSI(14): ",
                                    html.Strong("--", id=f"{index_id}-rsi-value"),
                                    " - ",
                                    html.Strong("--", id=f"{index_id}-rsi-label"),
                                ],
                                className="kpi-metric",
                            ),
                        ], 
                        className="kpi-metric-row"
                    ),
                    html.Span(
                        "Loading...",
                        id=f"{index_id}-badge",
                        className="mt-2 kpi-badge badge-slate",
                    )
                ],
                className="kpi-body",
            ),
        ],
        id=f"kpi-card-{index_id}",
        className="kpi-card",
    )


def update_index_card(
    technicals: dict,
    traffic_light: dict,
    strategy_label: str,
) -> tuple:
    """
    pdate an Index KPI card with latest technical values and regime styling.

    Args:
        technicals: Output from get_index_technicals().
        traffic_light: Output from index_traffic_light().
        strategy_label: Strategy text to show (e.g. "Short Calls" or "Cash-Secured Puts").

    Returns:
        Tuple of updated text values and CSS classNames in callback output order.
    """
    price = technicals.get("price", 0)
    sma20 = technicals.get("sma20", 0)
    sma50 = technicals.get("sma50", 0)
    sma100 = technicals.get("sma100", 0)
    rsi = technicals.get("rsi14", 0)
    rsi_label = technicals.get("rsi_label", "N/A")

    color = traffic_light.get("color", "slate")
    badge_text = f"{color.capitalize()} for {strategy_label}" if color != "slate" else "N/A"

    index_accent_class_name = f"kpi-accent {_ACCENT_COLOR_MAP.get(color, 'accent-slate')}"
    index_icon_class_name = f"bi bi-graph-up-arrow kpi-icon {_ICON_COLOR_MAP.get(color, 'icon-slate')}"
    index_badge_class_name = f"mt-2 kpi-badge {_BADGE_COLOR_MAP.get(color, 'badge-slate')}"

    return (
        f"{price:,.2f}",
        f"{sma20:,.0f}",
        f"{sma50:,.0f}",
        f"{sma100:,.0f}",
        f"{rsi:,.0f}",
        f"{rsi_label}",
        badge_text,
        index_accent_class_name,
        index_icon_class_name,
        index_badge_class_name,
    )
