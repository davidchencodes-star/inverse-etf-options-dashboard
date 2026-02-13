"""
Chain interaction callbacks.

Handles ETF selector changes, expiration selector changes, and
filter input changes to update the option chain table.

When the strategy toggle changes, the S&P 500 and Nasdaq index cards
are updated so their regime badge (e.g. "Red for Short Calls" vs
"Red for Cash-Secured Puts") reflects the selected strategy.
"""

import pandas as pd
from dash import Input, Output

from calculations.options_analytics import enrich_chain
from calculations.technicals import get_index_technicals
from calculations.traffic_lights import (
    index_traffic_light,
    option_traffic_light,
    vix_traffic_light,
)
from components.kpi_index import update_index_card
from components.option_chain_table import prepare_chain_data
from data.fetch import get_config, get_market_data


def register_chain_callbacks(app):
    """Register chain interaction callbacks."""

    @app.callback(
        Output("option-chain-table", "data", allow_duplicate=True),
        Output("option-chain-table", "style_data_conditional", allow_duplicate=True),
        Output("option-chain-table", "tooltip_data", allow_duplicate=True),
        Output("option-chain-table", "selected_rows"),
        Input("strategy-toggle", "value"),
        Input("etf-selector", "value"),
        Input("expiration-selector", "value"),
        Input("filter-min-return", "value"),
        Input("filter-min-oi", "value"),
        Input("filter-min-volume", "value"),
        prevent_initial_call=True,
    )
    def update_chain_on_control_change(
        strategy, selected_etf, selected_dte, min_return, min_oi, min_volume
    ):
        """Update chain table immediately when controls change."""
        config = get_config()
        market_data = get_market_data()

        quotes = market_data.get("quotes", {})
        chains = market_data.get("chains", {})
        historical = market_data.get("historical", {})

        strategy = strategy or "short_calls"
        selected_etf = selected_etf or config.get("etfs", ["SPXS"])[0]
        selected_dte = selected_dte or 7

        # Get VIX and index traffic light colors
        vix_quote = quotes.get(config.get("vix_symbol", "^VIX"), {})
        vix_level = vix_quote.get("last", 0)
        vix_tl = vix_traffic_light(vix_level, config)

        # Index technicals
        sp_symbol = config.get("index_proxies", {}).get("sp500", "SPY")
        ndx_symbol = config.get("index_proxies", {}).get("nasdaq", "QQQ")

        sp_hist = historical.get(sp_symbol)
        ndx_hist = historical.get(ndx_symbol)

        sp_techs = get_index_technicals(sp_hist if sp_hist is not None else pd.DataFrame())
        ndx_techs = get_index_technicals(ndx_hist if ndx_hist is not None else pd.DataFrame())

        sp_tl = index_traffic_light(sp_techs, strategy, config)
        ndx_tl = index_traffic_light(ndx_techs, strategy, config)

        # Get underlying price
        underlying_price = quotes.get(selected_etf, {}).get("last", 0)

        # Find the right chain
        etf_exps = market_data.get("expirations", {}).get(selected_etf, {})
        target_exp = etf_exps.get(selected_dte)

        if not target_exp:
            return [], [], [], []

        exp_key = str(target_exp)
        chain_df = chains.get(selected_etf, {}).get(exp_key)

        if chain_df is None or chain_df.empty:
            return [], [], [], []

        # Enrich
        enriched = enrich_chain(chain_df, underlying_price, config)

        # Filter by strategy
        if strategy == "short_calls":
            filtered = enriched[enriched["type"] == "call"].copy()
        else:
            filtered = enriched[enriched["type"] == "put"].copy()

        # Apply user filters
        if min_return is not None:
            filtered = filtered[filtered["ann_return"] >= float(min_return)]
        if min_oi is not None:
            filtered = filtered[filtered["openInterest"] >= int(min_oi)]
        if min_volume is not None:
            filtered = filtered[filtered["volume"] >= int(min_volume)]

        # Sort
        filtered = filtered.sort_values("ann_return", ascending=False)

        # Traffic lights
        idx_color = ndx_tl["color"] if selected_etf == "SQQQ" else sp_tl["color"]
        traffic_lights = []
        for _, row in filtered.iterrows():
            tl = option_traffic_light(row, vix_tl["color"], idx_color, config)
            traffic_lights.append(tl)

        table_data, style_cond, tooltip_data = prepare_chain_data(
            filtered.reset_index(drop=True), traffic_lights
        )

        return table_data, style_cond, tooltip_data, []  # Clear selection

    # Update S&P 500 and Nasdaq index cards when strategy changes (badge: "Red for Short Calls" etc.)
    @app.callback(
        Output("sp500-value", "children", allow_duplicate=True),
        Output("sp500-sma20-value", "children", allow_duplicate=True),
        Output("sp500-sma50-value", "children", allow_duplicate=True),
        Output("sp500-sma100-value", "children", allow_duplicate=True),
        Output("sp500-rsi-value", "children", allow_duplicate=True),
        Output("sp500-rsi-label", "children", allow_duplicate=True),
        Output("sp500-badge", "children", allow_duplicate=True),
        Output("sp500-accent", "className", allow_duplicate=True),
        Output("sp500-icon", "className", allow_duplicate=True),
        Output("sp500-badge", "className", allow_duplicate=True),
        Output("nasdaq-value", "children", allow_duplicate=True),
        Output("nasdaq-sma20-value", "children", allow_duplicate=True),
        Output("nasdaq-sma50-value", "children", allow_duplicate=True),
        Output("nasdaq-sma100-value", "children", allow_duplicate=True),
        Output("nasdaq-rsi-value", "children", allow_duplicate=True),
        Output("nasdaq-rsi-label", "children", allow_duplicate=True),
        Output("nasdaq-badge", "children", allow_duplicate=True),
        Output("nasdaq-accent", "className", allow_duplicate=True),
        Output("nasdaq-icon", "className", allow_duplicate=True),
        Output("nasdaq-badge", "className", allow_duplicate=True),
        Input("strategy-toggle", "value"),
        prevent_initial_call=True,
    )
    def update_index_cards_on_strategy_change(strategy):
        """Recompute index traffic lights and badge text for the selected strategy."""
        strategy = strategy or "short_calls"
        strategy_label = (
            "Short Calls" if strategy == "short_calls" else "Cash-Secured Puts"
        )
        config = get_config()
        market_data = get_market_data()
        historical = market_data.get("historical", {})

        sp_symbol = config.get("index_proxies", {}).get("sp500", "SPY")
        ndx_symbol = config.get("index_proxies", {}).get("nasdaq", "QQQ")
        sp_hist = historical.get(sp_symbol)
        ndx_hist = historical.get(ndx_symbol)

        sp_techs = get_index_technicals(
            sp_hist if sp_hist is not None else pd.DataFrame()
        )
        ndx_techs = get_index_technicals(
            ndx_hist if ndx_hist is not None else pd.DataFrame()
        )

        sp_tl = index_traffic_light(sp_techs, strategy, config)
        ndx_tl = index_traffic_light(ndx_techs, strategy, config)

        sp_out = update_index_card(sp_techs, sp_tl, strategy_label)
        ndx_out = update_index_card(ndx_techs, ndx_tl, strategy_label)

        return (*sp_out, *ndx_out)
