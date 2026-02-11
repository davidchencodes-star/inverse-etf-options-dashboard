"""
KPI Card 4: Inverse ETF Status -- 4-Level Card.

Shows which of SPXS, SQQQ, SH, SDS currently have attractive short options.
Each ETF gets a mini-row with ticker, price, green candidate count, and
a colored indicator dot.
"""

import dash_bootstrap_components as dbc
from dash import html

_DOT_STYLE = {
    "green": {"backgroundColor": "#28a745"},
    "yellow": {"backgroundColor": "#ffc107"},
    "red": {"backgroundColor": "#dc3545"},
}


def _status_dot(color: str) -> html.Span:
    """Create a small colored circle indicator."""
    base_style = {
        "display": "inline-block",
        "width": "12px",
        "height": "12px",
        "borderRadius": "50%",
        "marginLeft": "8px",
        "verticalAlign": "middle",
    }
    base_style.update(_DOT_STYLE.get(color, _DOT_STYLE["red"]))
    return html.Span(style=base_style)


def create_etf_status_card() -> dbc.Card:
    """Create the initial (empty) Inverse ETF Status card."""
    return dbc.Card(
        dbc.CardBody(
            [
                html.H6(
                    "Inverse ETF Status",
                    className="card-title text-muted mb-2",
                ),
                html.Div(id="etf-status-rows", children=[
                    html.P("Loading...", className="text-muted small"),
                ]),
                html.Hr(className="my-2"),
                html.P(
                    "--",
                    id="etf-status-summary",
                    className="small fw-bold mb-0",
                ),
            ]
        ),
        id="etf-status-card",
        className="h-100 shadow-sm",
    )


def build_etf_status_rows(etf_statuses: list[dict]) -> tuple:
    """
    Build the mini-rows and summary text for the ETF status card.

    Args:
        etf_statuses: List of dicts from etf_status_summary().

    Returns:
        (rows_children, summary_text)
    """
    rows = []
    summary_parts = []

    for etf in etf_statuses:
        symbol = etf["symbol"]
        price = etf["last_price"]
        green_calls = etf["green_calls"]
        green_puts = etf["green_puts"]
        total_green = etf["total_green"]
        color = etf["status_color"]

        # Build the row text
        if total_green > 0:
            count_text = f"{green_calls} green calls, {green_puts} green puts"
        else:
            count_text = "No qualifying contracts"

        row = html.Div(
            [
                html.Span(
                    f"{symbol} ",
                    className="fw-bold",
                ),
                html.Span(
                    f"{price:.2f}",
                    className="text-muted",
                ),
                html.Span(f" \u2013 {count_text}", className="small"),
                _status_dot(color),
            ],
            className="mb-1",
        )
        rows.append(row)
        summary_parts.append(f"{symbol} {total_green}")

    summary_text = "Total green candidates: " + " | ".join(summary_parts)

    return rows, summary_text
