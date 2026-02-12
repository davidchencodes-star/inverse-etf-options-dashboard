"""
Data refresh callback.

Handles both auto-refresh (dcc.Interval every 5 minutes) and
manual "Refresh Now" button clicks. Fetches all market data,
computes technicals, and updates all KPI cards + chain table.
"""

import logging
from datetime import datetime

import pandas as pd
from dash import Input, Output, State, callback, ctx, no_update

from calculations.options_analytics import enrich_chain
from calculations.technicals import get_index_technicals
from calculations.traffic_lights import (
    etf_status_summary,
    index_traffic_light,
    option_traffic_light,
    vix_traffic_light,
)
from components.kpi_etf_status import build_etf_status_rows
from components.kpi_index import update_index_card
from components.kpi_vix import update_vix_card
from components.option_chain_table import prepare_chain_data
from data.fetch import get_config, get_market_data, refresh_all

logger = logging.getLogger(__name__)


def register_data_refresh_callbacks(app):
    """Register all data refresh callbacks with the Dash app."""

    @app.callback(
        # VIX card outputs
        Output("vix-value", "children"),
        Output("vix-change", "children"),
        Output("vix-badge", "children"),
        Output("vix-accent", "className"),
        Output("vix-icon", "className"),
        Output("vix-badge", "className"),
        # S&P 500 card outputs
        Output("sp500-value", "children"),
        Output("sp500-sma20-value", "children"),
        Output("sp500-sma50-value", "children"),
        Output("sp500-sma100-value", "children"),
        Output("sp500-rsi-value", "children"),
        Output("sp500-rsi-label", "children"),
        Output("sp500-badge", "children"),
        Output("sp500-accent", "className"),
        Output("sp500-icon", "className"),
        Output("sp500-badge", "className"),
        # Nasdaq card outputs
        Output("nasdaq-value", "children"),
        Output("nasdaq-sma20-value", "children"),
        Output("nasdaq-sma50-value", "children"),
        Output("nasdaq-sma100-value", "children"),
        Output("nasdaq-rsi-value", "children"),
        Output("nasdaq-rsi-label", "children"),
        Output("nasdaq-badge", "children"),
        Output("nasdaq-accent", "className"),
        Output("nasdaq-icon", "className"),
        Output("nasdaq-badge", "className"),
        # ETF status card outputs
        Output("etf-status-list", "children"),
        Output("etf-status-summary", "children"),
        # Option chain table outputs
        Output("option-chain-table", "data"),
        Output("option-chain-table", "style_data_conditional"),
        Output("option-chain-table", "tooltip_data"),
        # Refresh text + stale warning
        Output("last-refresh-text", "children"),
        Output("stale-warning-store", "data"),
        # Inputs
        Input("auto-refresh-interval", "n_intervals"),
        Input("refresh-button", "n_clicks"),
        # State: current control selections
        State("strategy-toggle", "value"),
        State("etf-selector", "value"),
        State("expiration-selector", "value"),
        State("filter-min-return", "value"),
        State("filter-min-oi", "value"),
        State("filter-min-volume", "value"),
        prevent_initial_call=False,
    )
    def refresh_dashboard(
        n_intervals,
        n_clicks,
        strategy,
        selected_etf,
        selected_dte,
        min_return,
        min_oi,
        min_volume,
    ):
        """Main refresh callback -- fetches data and updates all dashboard components."""
        config = get_config()

        # Determine if this is a manual refresh
        triggered = ctx.triggered_id
        if triggered == "refresh-button":
            market_data = refresh_all()
        else:
            market_data = get_market_data()

        quotes = market_data.get("quotes", {})
        chains = market_data.get("chains", {})
        historical = market_data.get("historical", {})
        stale = market_data.get("stale_warning", False)
        last_refresh = market_data.get("last_refresh", datetime.now())

        strategy = strategy or "short_calls"
        selected_etf = selected_etf or config.get("etfs", ["SPXS"])[0]
        selected_dte = selected_dte or 7

        # Strategy label
        strategy_label = (
            "Short Calls" if strategy == "short_calls" else "Cash-Secured Puts"
        )

        # ---- VIX Card ----
        vix_quote = quotes.get(config.get("vix_symbol", "^VIX"), {})
        vix_level = vix_quote.get("last", 0)
        vix_change = vix_quote.get("change", 0)
        vix_change_pct = vix_quote.get("change_pct", 0)
        vix_tl = vix_traffic_light(vix_level, config)
        vix_out = update_vix_card(vix_level, vix_change, vix_change_pct, vix_tl)

        # ---- S&P 500 Card ----
        sp_symbol = config.get("index_proxies", {}).get("sp500", "SPY")
        sp_hist = historical.get(sp_symbol)
        if sp_hist is not None and not sp_hist.empty:
            sp_technicals = get_index_technicals(sp_hist)
        else:
            sp_technicals = get_index_technicals(pd.DataFrame())
        sp_tl = index_traffic_light(sp_technicals, strategy, config)
        sp_out = update_index_card(sp_technicals, sp_tl, strategy_label)

        # ---- Nasdaq Card ----
        ndx_symbol = config.get("index_proxies", {}).get("nasdaq", "QQQ")
        ndx_hist = historical.get(ndx_symbol)
        if ndx_hist is not None and not ndx_hist.empty:
            ndx_technicals = get_index_technicals(ndx_hist)
        else:
            ndx_technicals = get_index_technicals(pd.DataFrame())
        ndx_tl = index_traffic_light(ndx_technicals, strategy, config)
        ndx_out = update_index_card(ndx_technicals, ndx_tl, strategy_label)

        # ---- ETF Status Card ----
        underlying_prices = {
            etf: quotes.get(etf, {}).get("last", 0)
            for etf in config.get("etfs", [])
        }

        # Enrich all chains for status computation
        enriched_chains = {}
        for etf, etf_chains in chains.items():
            enriched_chains[etf] = {}
            for exp_key, chain_df in etf_chains.items():
                if not chain_df.empty:
                    enriched = enrich_chain(
                        chain_df, underlying_prices.get(etf, 0), config
                    )
                    enriched_chains[etf][exp_key] = enriched

        etf_statuses = etf_status_summary(
            enriched_chains,
            underlying_prices,
            vix_tl["color"],
            sp_tl["color"],
            ndx_tl["color"],
            strategy,
            config,
        )
        etf_list, etf_summary = build_etf_status_rows(etf_statuses)

        # ---- Option Chain Table ----
        # Get the enriched chain for the selected ETF and DTE
        etf_exps = market_data.get("expirations", {}).get(selected_etf, {})
        target_exp = etf_exps.get(selected_dte)

        table_data = []
        style_cond = []
        tooltip_data = []

        if target_exp:
            exp_key = str(target_exp)
            chain_df = enriched_chains.get(selected_etf, {}).get(exp_key)

            if chain_df is None:
                # Try raw chains if enrichment didn't happen
                chain_df = chains.get(selected_etf, {}).get(exp_key)
                if chain_df is not None and not chain_df.empty:
                    chain_df = enrich_chain(
                        chain_df, underlying_prices.get(selected_etf, 0), config
                    )

            if chain_df is not None and not chain_df.empty:
                # Apply user filters
                filtered = chain_df.copy()
                if min_return is not None:
                    filtered = filtered[filtered["ann_return"] >= float(min_return)]
                if min_oi is not None:
                    filtered = filtered[filtered["openInterest"] >= int(min_oi)]
                if min_volume is not None:
                    filtered = filtered[filtered["volume"] >= int(min_volume)]

                # Filter by strategy (show calls for short_calls, puts for cash_secured_puts)
                if strategy == "short_calls":
                    filtered = filtered[filtered["type"] == "call"]
                else:
                    filtered = filtered[filtered["type"] == "put"]

                # Sort by ann_return descending first, then compute traffic lights
                filtered = filtered.sort_values("ann_return", ascending=False)

                idx_color = (
                    ndx_tl["color"] if selected_etf == "SQQQ" else sp_tl["color"]
                )
                traffic_lights = []
                for _, row in filtered.iterrows():
                    tl = option_traffic_light(row, vix_tl["color"], idx_color, config)
                    traffic_lights.append(tl)

                table_data, style_cond, tooltip_data = prepare_chain_data(
                    filtered.reset_index(drop=True),
                    traffic_lights,
                )

        # ---- Refresh text ----
        refresh_text = f"Last: {last_refresh.strftime('%H:%M:%S')}"

        return (
            # VIX card (5 outputs)
            *vix_out,
            # S&P 500 card (6 outputs)
            *sp_out,
            # Nasdaq card (6 outputs)
            *ndx_out,
            # ETF status (2 outputs)
            etf_list,
            etf_summary,
            # Chain table (3 outputs)
            table_data,
            style_cond,
            tooltip_data,
            # Refresh (2 outputs)
            refresh_text,
            stale,
        )
