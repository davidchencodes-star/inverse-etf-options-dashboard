"""
Option Chain Panel with traffic-light indicator column.

Displays the full option chain as a DataTable with color-coded rows,
sorting, and row selection for KPI Card 5 integration.
"""

import dash_bootstrap_components as dbc
from dash import dash_table, html


# DataTable column definitions matching Spec Table 6
CHAIN_COLUMNS = [
    {"name": "",          "id": "traffic_light", "presentation": "markdown"},
    {"name": "Type",       "id": "type"},
    {"name": "Expiration", "id": "expiration"},
    {"name": "DTE",        "id": "dte",        "type": "numeric"},
    {"name": "Strike",     "id": "strike",     "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Bid",        "id": "bid",        "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Ask",        "id": "ask",        "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Mid",        "id": "mid",        "type": "numeric", "format": {"specifier": ".2f"}},
    {"name": "Delta",      "id": "delta",      "type": "numeric", "format": {"specifier": ".3f"}},
    {"name": "IV %",       "id": "iv_pct",     "type": "numeric", "format": {"specifier": ".1f"}},
    {"name": "Volume",     "id": "volume",     "type": "numeric"},
    {"name": "OI",         "id": "openInterest", "type": "numeric"},
    {"name": "Ann. Ret %", "id": "ann_return", "type": "numeric", "format": {"specifier": ".1f"}},
]


def create_option_chain_panel() -> html.Div:
    """Create the option chain panel with the DataTable."""
    return html.Div(
        [
            dash_table.DataTable(
                id="option-chain-table",
                columns=CHAIN_COLUMNS,
                data=[],
                sort_action="native",
                sort_by=[{"column_id": "ann_return", "direction": "desc"}],
                row_selectable="single",
                selected_rows=[],
                page_size=25,
                style_table={
                    "overflowX": "auto",
                    "minWidth": "100%",
                },
                style_header={
                    "backgroundColor": "#f8f9fa",
                    "fontWeight": "bold",
                    "fontSize": "13px",
                    "textAlign": "center",
                    "padding": "8px 6px",
                },
                style_cell={
                    "textAlign": "center",
                    "padding": "6px 8px",
                    "fontSize": "13px",
                    "minWidth": "60px",
                },
                style_cell_conditional=[
                    {"if": {"column_id": "traffic_light"}, "width": "40px", "minWidth": "40px"},
                    {"if": {"column_id": "type"}, "width": "55px"},
                    {"if": {"column_id": "contractSymbol"}, "textAlign": "left"},
                ],
                style_data_conditional=[],
                tooltip_data=[],
                tooltip_delay=0,
                tooltip_duration=None,
                css=[
                    # Make markdown column render without extra padding
                    {"selector": ".dash-cell div.dash-cell-value", "rule": "display: inline;"},
                ],
            ),
        ],
        className="mt-3",
    )


def prepare_chain_data(
    chain_df: "pd.DataFrame",
    traffic_lights: list[dict],
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Convert enriched chain DataFrame to DataTable format.

    Args:
        chain_df: Enriched chain DataFrame (from enrich_chain).
        traffic_lights: List of traffic light dicts (one per row).

    Returns:
        (table_data, style_data_conditional, tooltip_data)
    """
    if chain_df.empty:
        return [], [], []

    table_data = []
    style_cond = []
    tooltip_data = []

    for i, (_, row) in enumerate(chain_df.iterrows()):
        tl = traffic_lights[i] if i < len(traffic_lights) else {"color": "red", "tooltip": ""}
        color = tl["color"]
        tooltip = tl.get("tooltip", "")

        # Traffic light as colored circle using markdown
        if color == "green":
            dot = "\U0001F7E2"  # green circle emoji
        elif color == "yellow":
            dot = "\U0001F7E1"  # yellow circle emoji
        else:
            dot = "\U0001F534"  # red circle emoji

        # IV as percentage
        iv_raw = row.get("impliedVolatility", 0) or 0
        iv_pct = iv_raw * 100 if iv_raw < 5 else iv_raw  # Handle both decimal and % formats

        record = {
            "contractSymbol": str(row.get("contractSymbol", "")),
            "traffic_light": dot,
            "type": str(row.get("type", "")),
            "expiration": str(row.get("expiration", "")),
            "dte": int(row.get("dte", 0)),
            "strike": float(row.get("strike", 0)),
            "bid": float(row.get("bid", 0)),
            "ask": float(row.get("ask", 0)),
            "mid": float(row.get("mid", 0)),
            "delta": float(row.get("delta", 0)) if row.get("delta") is not None else None,
            "iv_pct": round(iv_pct, 1),
            "volume": int(row.get("volume", 0)),
            "openInterest": int(row.get("openInterest", 0)),
            "ann_return": float(row.get("ann_return", 0)),
        }
        table_data.append(record)

        # Row background tint based on traffic light
        bg_colors = {
            "green": "rgba(40, 167, 69, 0.08)",
            "yellow": "rgba(255, 193, 7, 0.08)",
            "red": "rgba(220, 53, 69, 0.06)",
        }
        style_cond.append(
            {
                "if": {"row_index": i},
                "backgroundColor": bg_colors.get(color, "transparent"),
            }
        )

        # Tooltip for the traffic light column
        tooltip_data.append(
            {
                "traffic_light": {"value": tooltip, "type": "text"},
            }
        )

    return table_data, style_cond, tooltip_data
