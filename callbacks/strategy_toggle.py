"""
Strategy toggle callback.

When the user switches between "Short Calls" and "Cash-Secured Puts",
this updates the S&P/Nasdaq KPI card colors, ETF status counts,
and the option chain table (re-filtering for calls vs puts).

NOTE: This logic is handled within the main data_refresh callback
to avoid circular dependencies. The strategy toggle is an input
to that callback. This module is kept as a placeholder for any
future strategy-specific logic that needs isolation.
"""


def register_strategy_callbacks(app):
    """
    Strategy toggle callbacks.

    Currently the strategy toggle is handled as a State input in the
    main data_refresh callback, which re-renders all components when
    the strategy changes. No additional callbacks needed here for now.

    Future: Could add strategy-specific analytics or persistence.
    """
    pass
