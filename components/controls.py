"""
Dashboard control bar.

Strategy toggle, ETF selector, expiration tabs, filter inputs,
and refresh controls. Placed above the option chain table.
"""

from datetime import datetime

import dash_bootstrap_components as dbc
from dash import dcc, html


def create_controls(config: dict) -> html.Div:
    """
    Create the control bar above the option chain.

    Args:
        config: Application configuration dict.
    """
    etfs = config.get("etfs", ["SPXS", "SQQQ", "SH", "SDS"])
    return_target = config.get("annualized_return_target", 30)
    delta_bands = config.get("delta_bands", {})
    liquidity = config.get("liquidity", {})
    refresh_min = config.get("refresh_interval_minutes", 5)

    call_focus = delta_bands.get("short_calls_focus", [0.20, 0.30])
    min_oi = liquidity.get("min_oi", 200)
    min_vol = liquidity.get("min_volume", 20)

    return html.Div(
        [
            dbc.Row(
                [
                    # Strategy toggle
                    dbc.Col(
                        [
                            html.Label(
                                "Strategy",
                                className="fw-bold small mb-1",
                            ),
                            dbc.RadioItems(
                                id="strategy-toggle",
                                options=[
                                    {"label": "Short Calls", "value": "short_calls"},
                                    {
                                        "label": "Cash-Secured Puts",
                                        "value": "cash_secured_puts",
                                    },
                                ],
                                value="short_calls",
                                inline=True,
                                className="mb-0",
                                inputClassName="me-1",
                                labelClassName="me-3 small",
                            ),
                        ],
                        md=3,
                        className="mb-2",
                    ),
                    # ETF selector
                    dbc.Col(
                        [
                            html.Label("ETF", className="fw-bold small mb-1"),
                            dbc.Select(
                                id="etf-selector",
                                options=[
                                    {"label": etf, "value": etf} for etf in etfs
                                ],
                                value=etfs[0] if etfs else "SPXS",
                                size="sm",
                            ),
                        ],
                        md=2,
                        className="mb-2",
                    ),
                    # Expiration selector
                    dbc.Col(
                        [
                            html.Label(
                                "Expiration",
                                className="fw-bold small mb-1",
                            ),
                            dbc.RadioItems(
                                id="expiration-selector",
                                options=[
                                    {"label": "~7 DTE", "value": 7},
                                    {"label": "~14 DTE", "value": 14},
                                ],
                                value=7,
                                inline=True,
                                className="mb-0",
                                inputClassName="me-1",
                                labelClassName="me-3 small",
                            ),
                        ],
                        md=2,
                        className="mb-2",
                    ),
                    # Filters
                    dbc.Col(
                        [
                            html.Label(
                                "Min Ann. Return %",
                                className="fw-bold small mb-1",
                            ),
                            dbc.Input(
                                id="filter-min-return",
                                type="number",
                                value=return_target,
                                min=0,
                                max=200,
                                step=5,
                                size="sm",
                            ),
                        ],
                        md=1,
                        className="mb-2",
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                "Min OI",
                                className="fw-bold small mb-1",
                            ),
                            dbc.Input(
                                id="filter-min-oi",
                                type="number",
                                value=min_oi,
                                min=0,
                                step=50,
                                size="sm",
                            ),
                        ],
                        md=1,
                        className="mb-2",
                    ),
                    dbc.Col(
                        [
                            html.Label(
                                "Min Vol",
                                className="fw-bold small mb-1",
                            ),
                            dbc.Input(
                                id="filter-min-volume",
                                type="number",
                                value=min_vol,
                                min=0,
                                step=5,
                                size="sm",
                            ),
                        ],
                        md=1,
                        className="mb-2",
                    ),
                    # Refresh controls
                    dbc.Col(
                        [
                            html.Label("\u00A0", className="fw-bold small mb-1 d-block"),
                            dbc.Button(
                                [html.I(className="me-1"), "Refresh Now"],
                                id="refresh-button",
                                color="primary",
                                size="sm",
                                className="w-100",
                            ),
                            html.Small(
                                "Last: --",
                                id="last-refresh-text",
                                className="text-muted d-block mt-1",
                            ),
                        ],
                        md=2,
                        className="mb-2",
                    ),
                ],
                className="align-items-end",
            ),
            # Auto-refresh interval
            dcc.Interval(
                id="auto-refresh-interval",
                interval=refresh_min * 60 * 1000,  # milliseconds
                n_intervals=0,
            ),
            # Hidden store for stale warning state
            dcc.Store(id="stale-warning-store", data=False),
        ],
        className="bg-light p-3 rounded shadow-sm",
    )
