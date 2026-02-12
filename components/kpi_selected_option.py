"""
Selected Option Performance Card

Shows detailed metrics for an option contract selected from the chain table.
Populated on row click; initially empty.
"""

from dash import html


def create_selected_option_card() -> html.Div:
    """Create Selected Option Performance card."""
    return html.Div(
        [
            html.Div(id="selected-option-accent", className="kpi-accent accent-slate"),
            html.Div(
                [
                    html.P(
                        [
                            html.I(
                                id="selected-option-icon",
                                className="bi bi-check-circle-fill kpi-icon icon-green",
                            ),
                            "Selected Option",
                        ],
                        className="kpi-title",
                    )
                ],
                className="kpi-header",
            ),
            html.Div(
                [
                    html.P(
                        "Click a row in the chain",
                        id="selected-option-value",
                        className="",
                    ),
                    html.P(
                        id="selected-option-detail",
                        className="",
                    ),
                    html.P(
                        id="selected-option-liquidity",
                        className="",
                    ),
                ],
                className="kpi-body",
            ),
        ],
        id="kpi-card-selected-option",
        className="kpi-card",
    )


def update_selected_option_card(
    option_data: dict,
    performance_color: dict,
    strategy_label: str,
) -> tuple:
    """
    Update Selected Option Performance card with contract details and styling.

    Args:
        option_data: Dict with option metrics from chain row (ann_return, dte, delta, IV, etc.).
        performance_color: Dict from selected_option_color() with 'color' key.
        strategy_label: Strategy name ('Short Call' or 'Cash-Secured Put').

    Returns:
        Tuple of 4 items for updating card components:
        (value_children, detail_children, liquidity_text, accent_class)
        value_children and detail_children may be Dash components (e.g. list of html.Span).
    """

    color = performance_color.get("color", "slate")
    if color not in ["green", "yellow", "red", "slate"]:
        color = "slate"

    ann_return = option_data.get("ann_return", 0)
    dte = option_data.get("dte", 0)
    delta = option_data.get("delta", "N/A")
    iv = option_data.get("impliedVolatility", 0)
    oi = option_data.get("openInterest", 0)
    volume = option_data.get("volume", 0)
    symbol = option_data.get("contractSymbol", "")

    # Format IV as percentage
    iv_pct = iv * 100 if iv and iv < 1 else (iv if iv else 0)

    # Folded "Ann. return:" label + colored percentage (no "(Green)" text)
    value_children = [
        html.Span("Ann. return: ", className="font-semibold mr-1"),
        html.Span(
            f"{ann_return:.1f}%",
            className=f"font-semibold etf-text-{color}",
        ),
    ]

    # Format delta display
    if delta is not None and delta != "N/A":
        delta_str = f"\u0394 {delta:.2f}"
    else:
        delta_str = "\u0394 N/A"

    # Strategy as label badge (neutral), then symbol | DTE | Δ | IV
    detail_children = [
        html.Span(strategy_label, className="selected-option-strategy-badge"),
        html.Span(f" {symbol} | {dte} DTE | {delta_str} | IV {iv_pct:.0f}%", className="selected-option-detail-rest"),
    ]

    liquidity_text = f"OI {oi:,} | Vol {volume:,}"

    return (
        value_children,
        detail_children,
        liquidity_text,
        f"kpi-accent accent-{color}",
    )
