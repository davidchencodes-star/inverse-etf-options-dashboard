"""
Inverse ETF Status Card

Displays short-option opportunities for SPXS, SQQQ, SH, and SDS with price,
candidate count, and regime indicator for each ETF.
"""

from dash import html


def create_etf_status_card() -> html.Div:
    """Create Inverse ETF Status KPI card."""
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
    Build display rows and summary for Inverse ETF Status card.

    Args:
        etf_statuses: List of ETF status dicts from etf_status_summary().

    Returns:
        Tuple of (rows_children, summary_text):
            rows_children: List of html.Li elements for each ETF
            summary_text: String summarizing total candidates across all ETFs
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

        if (color not in ["green", "yellow", "red"]):
            color = "red"

        if total_green > 0:
            count_text = f"{green_calls} Green Calls, {green_puts} Green Puts"
        else:
            count_text = "No Qualifying Contracts"

        row = html.Li(
            [
                html.Div(
                    [
                        html.Span(className=f"dot dot-{color}"),
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
