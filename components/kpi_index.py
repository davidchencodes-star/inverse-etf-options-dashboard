"""
S&P 500 / Nasdaq Technical Regime Cards

Displays index price, SMA(20/50/100), RSI(14), and strategy-adaptive regime indicator
for Short Calls and Cash-Secured Puts strategies.
"""

from dash import html


def create_index_card(index_id: str, title: str) -> html.Div:
    """
    Create Index Technical Regime KPI card with default slate styling.

    Args:
        index_id: Prefix for component IDs (e.g. 'sp500' or 'nasdaq').
        title: Card title (e.g. 'S&P 500 Technical').
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
    Update Index KPI card with latest technical values and regime styling.

    Args:
        technicals: Dict from get_index_technicals() with price, SMA, and RSI values.
        traffic_light: Dict from index_traffic_light() with 'color' key.
        strategy_label: Strategy name (e.g. 'Short Calls' or 'Cash-Secured Puts').

    Returns:
        Tuple of 10 strings for updating card components:
        (price, sma20, sma50, sma100, rsi, rsi_label, badge_text, 
         accent_class, icon_class, badge_class)
    """
    price = technicals.get("price", 0)
    sma20 = technicals.get("sma20", 0)
    sma50 = technicals.get("sma50", 0)
    sma100 = technicals.get("sma100", 0)
    rsi = technicals.get("rsi14", 0)
    rsi_label = technicals.get("rsi_label", "N/A")

    color = traffic_light.get("color", "slate")
    if (color not in ["green", "yellow", "red", "slate"]):
        color = "slate"

    badge_text = f"{color.capitalize()} for {strategy_label}" if color != "slate" else "N/A"

    return (
        f"{price:,.2f}",
        f"{sma20:,.0f}",
        f"{sma50:,.0f}",
        f"{sma100:,.0f}",
        f"{rsi:.0f}",
        rsi_label,
        badge_text,
        f"kpi-accent accent-{color}",
        f"bi bi-graph-up-arrow kpi-icon icon-{color}",
        f"mt-2 kpi-badge badge-{color}",
    )
