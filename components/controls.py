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
            html.Div(id="controls-accent", className="kpi-accent accent-slate"),
            html.Div(
                [
                    html.P(
                        [
                            html.I(
                                id="controls-icon",
                                className="bi bi-sliders kpi-icon icon-slate",
                            ),
                            "Strategy Filters",
                        ],
                        className="kpi-title",
                    ),
                    html.Span(
                        "Last: --",
                        id="last-refresh-text"
                    )
                ],
                className="kpi-header d-flex align-items-center justify-content-between gap-2",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Div("Strategy", className="small text-muted fw-semibold mb-1"),
                            dbc.RadioItems(
                                id="strategy-toggle",
                                options=[
                                    {"label": html.Span([html.I(className="bi bi-arrow-down-right me-2"), "Short Calls"]),
                                    "value": "short_calls"},
                                    {"label": html.Span([html.I(className="bi bi-shield-check me-2"), "Cash-Secured Puts"]),
                                    "value": "cash_secured_puts"},
                                ],
                                value="short_calls",   # set default
                                inline=True,
                                className="segmented w-100",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-secondary flex-fill text-center",
                                labelCheckedClassName="active",
                            ),
                        ],
                        xs=12,
                    ),
                    dbc.Col(
                        [
                            html.Div("ETF", className="small text-muted fw-semibold mb-1"),
                            dbc.Select(
                                id="etf-selector",
                                options=[{"label": etf, "value": etf} for etf in etfs],
                                value=etfs[0] if etfs else "SPXS",
                            ),
                        ],
                        xs=12, md=6,
                    ),
                    dbc.Col(
                        [
                            html.Div("Expiration", className="small text-muted fw-semibold mb-1"),
                            dbc.RadioItems(
                                id="expiration-selector",
                                options=[
                                    {"label": "~7 DTE", "value": 7},
                                    {"label": "~14 DTE", "value": 14},
                                ],
                                value=7,
                                inline=True,
                                className="segmented w-100",
                                inputClassName="btn-check",
                                labelClassName="btn btn-outline-secondary flex-fill text-center",
                                labelCheckedClassName="active",
                            ),
                        ],
                        xs=12, md=6,
                    ),
                    dbc.Col(
                        [
                            html.Div("Thresholds", className="small text-muted fw-semibold mb-1"),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            html.Label("Min Ann. Return %", className="form-label text-muted small mb-1"),
                                            dbc.Input(
                                                id="filter-min-return",
                                                type="number",
                                                value=return_target,
                                                min=0,
                                                max=200,
                                                step=5,
                                            ),
                                        ],
                                        xs=12, md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Min OI", className="form-label text-muted small mb-1"),
                                            dbc.Input(
                                                id="filter-min-oi",
                                                type="number",
                                                value=min_oi,
                                                min=0,
                                                step=50,
                                            ),
                                        ],
                                        xs=12, md=4,
                                    ),
                                    dbc.Col(
                                        [
                                            html.Label("Min Vol", className="form-label text-muted small mb-1"),
                                            dbc.Input(
                                                id="filter-min-volume",
                                                type="number",
                                                value=min_vol,
                                                min=0,
                                                step=5,
                                            ),
                                        ],
                                        xs=12, md=4,
                                    ),
                                ],
                                className="g-2",
                            ),
                        ],
                        xs=12,
                        className="d-none",
                    ),
                    dbc.Col(
                        [
                            dbc.Button(
                                [
                                    html.I(className="bi bi-arrow-repeat me-2"),
                                    "Refresh Now",
                                ],
                                id="refresh-button",
                                className="btn-dark w-100 py-2 rounded",
                            )
                        ],
                        xs=12,
                    )
                ],
                className="kpi-body g-3",
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
        id="kpi-card-controls",
        className="kpi-card",
    )
