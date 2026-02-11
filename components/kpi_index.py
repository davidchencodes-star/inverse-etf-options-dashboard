"""
KPI Cards 2 & 3: S&P 500 / Nasdaq Technical Regime -- SMA + RSI Traffic Light.

Displays index price, SMA 20/50/100 values, RSI(14), and a colored status
pill whose color adapts based on the selected strategy (Short Calls vs CSP).
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


def create_index_card(index_id: str, title: str) -> dbc.Card:
    """
    Create an index technical regime KPI card.

    Args:
        index_id: Prefix for component IDs (e.g. 'sp500' or 'nasdaq').
        title: Card title (e.g. 'S&P 500 Technical').
    """
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(title, className="card-title text-muted mb-1"),
                html.H3("--", id=f"{index_id}-price", className="mb-1"),
                html.P(
                    "--",
                    id=f"{index_id}-sma-line",
                    className="small mb-1",
                    style={"fontFamily": "monospace"},
                ),
                html.P(
                    "--",
                    id=f"{index_id}-rsi-line",
                    className="small mb-2",
                ),
                dbc.Badge(
                    "Loading...",
                    id=f"{index_id}-badge",
                    color="secondary",
                    className="px-3 py-2",
                ),
            ]
        ),
        id=f"{index_id}-card",
        className="h-100 shadow-sm",
    )


def update_index_card(
    technicals: dict,
    traffic_light: dict,
    strategy_label: str,
) -> tuple:
    """
    Return updated values for an index KPI card.

    Args:
        technicals: Dict from get_index_technicals().
        traffic_light: Dict from index_traffic_light().
        strategy_label: "Short Calls" or "Cash-Secured Puts".

    Returns:
        (price_text, sma_line, rsi_line, badge_text, badge_color, card_class)
    """
    price = technicals.get("price", 0)
    sma20 = technicals.get("sma20", 0)
    sma50 = technicals.get("sma50", 0)
    sma100 = technicals.get("sma100", 0)
    rsi = technicals.get("rsi14", 0)
    rsi_label = technicals.get("rsi_label", "N/A")

    color = traffic_light.get("color", "yellow")
    label = traffic_light.get("label", "")

    # SMA checkmarks
    def sma_indicator(above: bool) -> str:
        return "\u2713" if above else "\u2717"

    sma_line = (
        f"SMA20: {sma20:,.0f} {sma_indicator(technicals.get('above_sma20', False))} | "
        f"SMA50: {sma50:,.0f} {sma_indicator(technicals.get('above_sma50', False))} | "
        f"SMA100: {sma100:,.0f} {sma_indicator(technicals.get('above_sma100', False))}"
    )
    rsi_line = f"RSI(14): {rsi:.0f} \u2013 {rsi_label}"

    badge_variant = _COLOR_MAP.get(color, "secondary")
    border_class = _BORDER_MAP.get(color, "")

    badge_text = f"{color.capitalize()} for {strategy_label}"

    return (
        f"{price:,.2f}",
        sma_line,
        rsi_line,
        badge_text,
        badge_variant,
        f"h-100 shadow-sm {border_class}",
    )
