"""
Strategy Payoff Preview Chart.

Displays a simple P/L chart at expiration for the selected short option
(short call or cash-secured put). Shows breakeven point annotated.
"""

import plotly.graph_objects as go
from dash import dcc, html


def create_payoff_panel() -> html.Div:
    """Create the placeholder for the payoff chart."""
    return html.Div(
        [
            html.H6(
                "Payoff at Expiration",
                className="text-muted mb-2 mt-3",
            ),
            dcc.Graph(
                id="payoff-chart",
                config={"displayModeBar": False},
                style={"height": "280px"},
                figure=_empty_figure(),
            ),
        ]
    )


def _empty_figure() -> go.Figure:
    """Return an empty placeholder figure."""
    fig = go.Figure()
    fig.update_layout(
        template="plotly_white",
        margin=dict(l=40, r=20, t=20, b=40),
        xaxis_title="Underlying Price at Expiry",
        yaxis_title="P/L ($)",
        height=280,
        annotations=[
            dict(
                text="Select an option from the chain to view payoff",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=14, color="gray"),
            )
        ],
    )
    return fig


def build_payoff_figure(
    payoff_df: "pd.DataFrame",
    breakeven: float,
    option_type: str,
    strike: float,
    premium: float,
) -> go.Figure:
    """
    Build the payoff chart for a short option position.

    Args:
        payoff_df: DataFrame with columns: underlying_at_expiry, pnl.
        breakeven: Breakeven price.
        option_type: 'call' or 'put'.
        strike: Strike price.
        premium: Premium collected.

    Returns:
        Plotly Figure.
    """
    fig = go.Figure()

    prices = payoff_df["underlying_at_expiry"]
    pnl = payoff_df["pnl"]

    # Color-fill: green for profit, red for loss
    fig.add_trace(
        go.Scatter(
            x=prices,
            y=pnl,
            mode="lines",
            line=dict(color="#333333", width=2),
            name="P/L",
            fill="tozeroy",
            fillcolor="rgba(40, 167, 69, 0.15)",
        )
    )

    # Highlight loss region
    loss_mask = pnl < 0
    if loss_mask.any():
        fig.add_trace(
            go.Scatter(
                x=prices[loss_mask],
                y=pnl[loss_mask],
                mode="lines",
                line=dict(color="transparent"),
                fill="tozeroy",
                fillcolor="rgba(220, 53, 69, 0.15)",
                showlegend=False,
            )
        )

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", line_width=1)

    # Breakeven annotation
    fig.add_vline(
        x=breakeven,
        line_dash="dot",
        line_color="#6c757d",
        annotation_text=f"BE: {breakeven:.2f}",
        annotation_position="top right",
        annotation_font_size=11,
    )

    # Strike annotation
    fig.add_vline(
        x=strike,
        line_dash="dash",
        line_color="#0d6efd",
        annotation_text=f"Strike: {strike:.2f}",
        annotation_position="bottom right",
        annotation_font_size=11,
    )

    # Max profit annotation
    fig.add_annotation(
        x=strike,
        y=premium,
        text=f"Max Profit: ${premium:.2f}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        font=dict(size=11, color="#28a745"),
    )

    strategy_name = "Short Call" if option_type == "call" else "Short Put"

    fig.update_layout(
        template="plotly_white",
        margin=dict(l=50, r=20, t=30, b=50),
        xaxis_title="Underlying Price at Expiry",
        yaxis_title="P/L ($)",
        height=280,
        showlegend=False,
        title=dict(
            text=f"{strategy_name} | Strike {strike:.2f} | Premium ${premium:.2f}",
            font=dict(size=13),
            x=0.5,
        ),
    )

    return fig
