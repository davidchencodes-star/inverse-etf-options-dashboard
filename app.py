"""
Inverse ETF Options Dashboard
==============================
Systematic short premium selling dashboard for inverse ETFs (SPXS, SQQQ, SH, SDS).

Provides VIX regime monitoring, S&P 500/Nasdaq technical analysis (SMA + RSI),
option chain analysis with traffic-light indicators, and payoff previews.

Run:
    python app.py
    Then open http://127.0.0.1:8050/ in your browser.
"""

import logging

import dash
import dash_bootstrap_components as dbc
from dash import html, dcc

from callbacks.chain_interaction import register_chain_callbacks
from callbacks.data_refresh import register_data_refresh_callbacks
from callbacks.option_selection import register_option_selection_callbacks
from callbacks.strategy_toggle import register_strategy_callbacks
from components.controls import create_controls
from components.kpi_etf_status import create_etf_status_card
from components.kpi_index import create_index_card
from components.kpi_selected_option import create_selected_option_card
from components.kpi_vix import create_vix_card
from components.option_chain_table import create_option_chain_panel
from components.payoff_chart import create_payoff_panel
from data.fetch import get_config

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App Initialization
# ---------------------------------------------------------------------------
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.FLATLY,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css"
    ],
    title="Inverse ETF Options Dashboard",
    update_title="Refreshing...",
    suppress_callback_exceptions=True,
)

server = app.server  # For deployment (gunicorn, etc.)

# ---------------------------------------------------------------------------
# Load Config
# ---------------------------------------------------------------------------
config = get_config()

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
app.layout = dbc.Container(
    [
        # --- Header ---
        dbc.Row(
            dbc.Col(
                [
                    html.H1(
                        "Inverse ETF Options Dashboard",
                        className="dashboard-title mb-0 mt-3",
                    ),
                    html.P(
                        "Short Calls & Cash-Secured Puts | SPXS \u2022 SQQQ \u2022 SH \u2022 SDS",
                        className="dashboard-subtitle mb-3",
                    ),
                ],
            ),
        ),

        # --- Stale Data Warning Banner ---
        html.Div(
            [
                html.Span("\u26A0\uFE0F"),
                html.Span(
                    "Data may be stale \u2013 some API requests failed. "
                    "Showing cached data. Click 'Refresh Now' to retry."
                ),
            ],
            id="stale-banner",
            className="stale-banner hidden mb-3",
        ),

        # --- KPI Cards Row ---
        dbc.Row(
            [
                dbc.Col(create_vix_card(), lg=3, className="mb-3"),
                dbc.Col(
                    create_index_card("sp500", "S&P 500 Technical"),
                    lg=3, className="mb-3",
                ),
                dbc.Col(
                    create_index_card("nasdaq", "Nasdaq Technical"),
                    lg=3, className="mb-3",
                ),
                dbc.Col(create_etf_status_card(), lg=3, className="mb-3"),
            ],
            className="g-3",
        ),

        dbc.Row(
            [
                dbc.Col(create_selected_option_card(), lg=6, className="mb-3"),
            ],
            className="g-3",
        ),

        # --- Controls Bar ---
        create_controls(config),

        # --- Option Chain Table ---
        create_option_chain_panel(),

        # --- Payoff Chart ---
        create_payoff_panel(),

        # --- Footer ---
        html.Hr(className="mt-4"),
        html.P(
            [
                html.Small(
                    "Data: yfinance (15-min delayed) | "
                    "All thresholds configurable in config.yaml | "
                    "Phase 1 \u2013 v1.0",
                    className="text-muted",
                ),
            ],
            className="text-center mb-3",
        ),

        # --- Hidden callback to show/hide stale banner ---
        dcc.Store(id="stale-banner-trigger"),
    ],
    fluid=True,
    className="px-4",
)

# ---------------------------------------------------------------------------
# Register Callbacks
# ---------------------------------------------------------------------------
register_data_refresh_callbacks(app)
register_chain_callbacks(app)
register_option_selection_callbacks(app)
register_strategy_callbacks(app)


# --- Stale banner visibility callback ---
@app.callback(
    dash.Output("stale-banner", "className"),
    dash.Input("stale-warning-store", "data"),
)
def toggle_stale_banner(is_stale):
    """Show or hide the stale data warning banner."""
    if is_stale:
        return "stale-banner mb-3"
    return "stale-banner hidden mb-3"

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logger.info("Starting Inverse ETF Options Dashboard...")
    logger.info("Open http://127.0.0.1:8050/ in your browser")
    app.run(debug=True, host="127.0.0.1", port=8050, use_reloader=False)
