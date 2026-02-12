"""
KPI Card 4: Inverse ETF Status (4-Level Card)

Shows whether SPXS, SQQQ, SH, and SDS currently have attractive short-option candidates.
Each ETF is displayed as a mini-row with ticker, last price, candidate count, and a color-coded status dot.
"""

from dash import html

_DOT_COLOR_MAP = {
    "green": "dot-green",
    "yellow": "dot-yellow",
    "red": "dot-red",
}


def create_etf_status_card() -> html.Div:
    """Create the initial (empty) Inverse ETF Status KPI card."""
    return html.Div(
        [
            html.Div("", id="etf-status-accent", className="kpi-accent accent-slate"),
            html.Div(
                [
                    html.P(
                        [
                            html.I(
                                id="etf-status-icon",
                                className="bi bi-activity kpi-icon icon-slate",
                            ),
                            "Inverse ETF Status",
                        ],
                        className="kpi-title",
                    )
                ],
                className="kpi-header",
            ),
            html.Div(
                [
                    html.Ul(id="etf-status-list", className="status-list"),
                    html.P(id="etf-status-summary", className="status-summary"),
                ],
                className="kpi-body",
            ),
        ],
        id="kpi-card-etf-status",
        className="kpi-card",
    )


def build_etf_status_rows(etf_statuses: list[dict]) -> tuple:
    """
    Build the mini-rows and summary text for the Inverse ETF Status card.

    Args:
        etf_statuses: Output from etf_status_summary(); a list of per-ETF status items.

    Returns:
        tuple[list, str]:
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

        row = html.Li(
            [
                html.Div(
                    [
                        html.Span(className=f"dot {_DOT_COLOR_MAP.get(color, 'dot-red')}"),
                        html.Span(symbol, className="ticker"),
                        html.Span(count_text, className="status-text"),
                    ],
                    className="status-left",
                ),
                html.Span(f"{price:,.2f}", className="price"),
            ],
            className="status-item",
        )
        rows.append(row)
        summary_parts.append(f"{symbol} {total_green}")

    summary_text = "Total green candidates: " + " | ".join(summary_parts)

    return rows, summary_text
