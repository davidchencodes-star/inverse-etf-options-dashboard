"""
Option selection callback.

When a row is clicked in the option chain DataTable, this updates:
- KPI Card 5 (Selected Option Performance)
- Payoff chart
"""

from dash import Input, Output, State, callback, no_update

from calculations.options_analytics import compute_payoff_table
from calculations.traffic_lights import selected_option_color
from components.kpi_selected_option import update_selected_option_card
from components.payoff_chart import build_payoff_figure
from data.fetch import get_config, get_market_data


def register_option_selection_callbacks(app):
    """Register option selection callbacks."""

    @app.callback(
        # KPI Card 5 outputs
        Output("selected-option-value", "children"),
        Output("selected-option-detail", "children"),
        Output("selected-option-liquidity", "children"),
        Output("selected-option-accent", "className"),
        # Payoff chart
        Output("payoff-chart", "figure"),
        # Inputs
        Input("option-chain-table", "selected_rows"),
        State("option-chain-table", "data"),
        State("strategy-toggle", "value"),
        prevent_initial_call=True,
    )
    def on_option_selected(selected_rows, table_data, strategy):
        """Handle row selection in the option chain table."""
        if not selected_rows or not table_data:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        row_idx = selected_rows[0]
        if row_idx >= len(table_data):
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

        row = table_data[row_idx]
        config = get_config()

        # Build option_data dict
        option_data = {
            "contractSymbol": row.get("contractSymbol", ""),
            "type": row.get("type", ""),
            "expiration": row.get("expiration", ""),
            "dte": row.get("dte", 0),
            "strike": row.get("strike", 0),
            "bid": row.get("bid", 0),
            "ask": row.get("ask", 0),
            "mid": row.get("mid", 0),
            "delta": row.get("delta"),
            "impliedVolatility": row.get("iv_pct", 0) / 100 if row.get("iv_pct") else 0,
            "volume": row.get("volume", 0),
            "openInterest": row.get("openInterest", 0),
            "ann_return": row.get("ann_return", 0),
        }

        # Determine performance color
        perf_color = selected_option_color(
            ann_return=option_data["ann_return"],
            oi=option_data["openInterest"],
            volume=option_data["volume"],
            config=config,
        )

        # Strategy label
        strategy_label = (
            "Short Call" if strategy == "short_calls" else "Cash-Secured Put"
        )

        # Update KPI Card 5
        card_out = update_selected_option_card(
            option_data, perf_color, strategy_label
        )

        # Build payoff chart
        premium = option_data["mid"]
        strike = option_data["strike"]
        option_type = option_data["type"]

        # Get the actual underlying price for the payoff range
        market_data = get_market_data()
        # Extract ETF symbol from contract symbol (e.g., "SPXS260218C00025000" -> "SPXS")
        contract = option_data.get("contractSymbol", "")
        etf_symbol = ""
        for etf in get_config().get("etfs", []):
            if contract.startswith(etf):
                etf_symbol = etf
                break
        underlying_price = (
            market_data.get("quotes", {}).get(etf_symbol, {}).get("last", strike)
            if etf_symbol else strike
        )

        if premium > 0 and strike > 0:
            payoff_df, breakeven = compute_payoff_table(
                option_type=option_type,
                strike=strike,
                premium=premium,
                underlying_price=underlying_price,
            )
            payoff_fig = build_payoff_figure(
                payoff_df, breakeven, option_type, strike, premium
            )
        else:
            from components.payoff_chart import _empty_figure
            payoff_fig = _empty_figure()

        return (*card_out, payoff_fig)
