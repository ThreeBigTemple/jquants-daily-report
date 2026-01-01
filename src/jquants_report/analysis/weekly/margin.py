"""Weekly margin trading analysis module.

Section 5: Margin Trading Trends
- Margin buy/sell balance
- Margin ratio
- Week-over-week changes
- Top margin stocks
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    MarginTradingData,
    TopMarginStock,
    WeeklyMarginTrends,
)

logger = logging.getLogger(__name__)


class WeeklyMarginAnalyzer:
    """Analyzer for weekly margin trading trends (Section 5)."""

    def analyze(
        self,
        week_end: date,
        margin_df: pd.DataFrame,
        prev_week_margin_df: pd.DataFrame | None = None,
        weekly_quotes: pd.DataFrame | None = None,
    ) -> WeeklyMarginTrends:
        """Analyze margin trading trends.

        Args:
            week_end: End date of the week.
            margin_df: Margin trading data for the week.
            prev_week_margin_df: Previous week's margin data.
            weekly_quotes: Weekly stock data for return information.

        Returns:
            WeeklyMarginTrends: Margin trading analysis.
        """
        overall = self._calculate_overall(
            week_end,
            margin_df,
            prev_week_margin_df,
        )

        top_margin_buy = self._get_top_margin_buy(margin_df, weekly_quotes)
        top_margin_sell = self._get_top_margin_sell(margin_df, weekly_quotes)

        return WeeklyMarginTrends(
            week_end=week_end,
            overall=overall,
            top_margin_buy=top_margin_buy,
            top_margin_sell=top_margin_sell,
        )

    def _calculate_overall(
        self,
        week_end: date,
        margin_df: pd.DataFrame,
        prev_week_df: pd.DataFrame | None,
    ) -> MarginTradingData:
        """Calculate overall margin trading statistics."""
        buy_balance = 0.0
        sell_balance = 0.0
        margin_ratio = 0.0

        if not margin_df.empty:
            # Get balance columns (may vary by API response)
            buy_col = None
            sell_col = None

            for col in margin_df.columns:
                if "Buy" in col and "Balance" in col:
                    buy_col = col
                elif "Sell" in col and "Balance" in col:
                    sell_col = col

            if buy_col:
                buy_balance = float(margin_df[buy_col].sum())
            if sell_col:
                sell_balance = float(margin_df[sell_col].sum())

            if sell_balance > 0:
                margin_ratio = buy_balance / sell_balance

        # Previous week comparison
        prev_buy = None
        prev_sell = None
        buy_change = None
        sell_change = None

        if prev_week_df is not None and not prev_week_df.empty:
            for col in prev_week_df.columns:
                if "Buy" in col and "Balance" in col:
                    prev_buy = float(prev_week_df[col].sum())
                elif "Sell" in col and "Balance" in col:
                    prev_sell = float(prev_week_df[col].sum())

            if prev_buy is not None:
                buy_change = buy_balance - prev_buy
            if prev_sell is not None:
                sell_change = sell_balance - prev_sell

        return MarginTradingData(
            week_end=week_end,
            margin_buy_balance=buy_balance,
            margin_sell_balance=sell_balance,
            margin_ratio=margin_ratio,
            prev_week_buy_balance=prev_buy,
            prev_week_sell_balance=prev_sell,
            buy_balance_change=buy_change,
            sell_balance_change=sell_change,
        )

    def _get_top_margin_buy(
        self,
        margin_df: pd.DataFrame,
        weekly_quotes: pd.DataFrame | None,
        top_n: int = 10,
    ) -> list[TopMarginStock]:
        """Get stocks with highest margin buy balance."""
        if margin_df.empty:
            return []

        # Find buy balance column
        buy_col = None
        for col in margin_df.columns:
            if "Buy" in col and "Balance" in col:
                buy_col = col
                break

        if buy_col is None:
            return []

        sorted_df = margin_df.sort_values(buy_col, ascending=False).head(top_n)
        return self._convert_to_top_stocks(sorted_df, buy_col, weekly_quotes)

    def _get_top_margin_sell(
        self,
        margin_df: pd.DataFrame,
        weekly_quotes: pd.DataFrame | None,
        top_n: int = 10,
    ) -> list[TopMarginStock]:
        """Get stocks with highest margin sell balance."""
        if margin_df.empty:
            return []

        # Find sell balance column
        sell_col = None
        for col in margin_df.columns:
            if "Sell" in col and "Balance" in col:
                sell_col = col
                break

        if sell_col is None:
            return []

        sorted_df = margin_df.sort_values(sell_col, ascending=False).head(top_n)
        return self._convert_to_top_stocks(sorted_df, sell_col, weekly_quotes)

    def _convert_to_top_stocks(
        self,
        df: pd.DataFrame,
        _primary_col: str,
        weekly_quotes: pd.DataFrame | None,
    ) -> list[TopMarginStock]:
        """Convert DataFrame to list of TopMarginStock."""
        stocks = []

        # Create return lookup
        return_lookup: dict[str, float] = {}
        if weekly_quotes is not None and not weekly_quotes.empty:
            for _, row in weekly_quotes.iterrows():
                code = str(row.get("Code", ""))
                ret = row.get("WeeklyReturn")
                if pd.notna(ret):
                    return_lookup[code] = float(ret)

        for _, row in df.iterrows():
            code = str(row.get("Code", ""))

            # Find buy and sell columns
            buy_balance = 0.0
            sell_balance = 0.0

            for col in df.columns:
                if "Buy" in col and "Balance" in col:
                    buy_balance = float(row.get(col, 0))
                elif "Sell" in col and "Balance" in col:
                    sell_balance = float(row.get(col, 0))

            margin_ratio = buy_balance / sell_balance if sell_balance > 0 else 0.0

            stocks.append(
                TopMarginStock(
                    code=code,
                    name=str(row.get("CompanyName", row.get("Name", "不明"))),
                    margin_buy_balance=buy_balance,
                    margin_sell_balance=sell_balance,
                    margin_ratio=margin_ratio,
                    weekly_return_pct=return_lookup.get(code),
                )
            )

        return stocks
