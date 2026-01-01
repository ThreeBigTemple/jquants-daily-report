"""Weekly data aggregator for J-Quants data.

This module provides functionality to aggregate daily data into weekly summaries,
reusing cached daily data to minimize API calls.
"""

import logging
from datetime import date, timedelta
from typing import Any

import pandas as pd

from jquants_report.data.cache import CacheManager

logger = logging.getLogger(__name__)


class WeeklyDataAggregator:
    """Aggregates daily data into weekly summaries.

    Leverages cached daily data to efficiently create weekly aggregations
    without redundant API calls.
    """

    def __init__(
        self,
        cache_manager: CacheManager,
        data_fetcher: Any = None,
    ):
        """Initialize WeeklyDataAggregator.

        Args:
            cache_manager: CacheManager instance for accessing cached data.
            data_fetcher: Optional DataFetcher for fetching missing data.
        """
        self.cache = cache_manager
        self.fetcher = data_fetcher

    def get_week_trading_days(self, week_end: date) -> list[date]:
        """Get trading days for a week ending on the specified date.

        Args:
            week_end: The Friday (or last trading day) of the week.

        Returns:
            List of trading dates from Monday to Friday (excluding weekends).
        """
        # Find Monday of that week
        days_since_monday = week_end.weekday()
        week_start = week_end - timedelta(days=days_since_monday)

        # Generate weekdays (Mon-Fri)
        trading_days = []
        for i in range(5):
            day = week_start + timedelta(days=i)
            if day <= week_end and day.weekday() < 5:  # Weekday only
                trading_days.append(day)

        return trading_days

    def get_previous_week_end(self, week_end: date) -> date:
        """Get the Friday of the previous week.

        Args:
            week_end: Current week's end date.

        Returns:
            Previous week's Friday.
        """
        # Find previous Friday
        days_to_friday = (week_end.weekday() - 4) % 7
        if days_to_friday == 0:
            days_to_friday = 7
        return week_end - timedelta(days=days_to_friday)

    def get_latest_friday(self, reference_date: date | None = None) -> date:
        """Get the most recent Friday.

        Args:
            reference_date: Reference date. Defaults to today.

        Returns:
            Most recent Friday date.
        """
        if reference_date is None:
            reference_date = date.today()

        days_since_friday = (reference_date.weekday() - 4) % 7
        return reference_date - timedelta(days=days_since_friday)

    def aggregate_daily_quotes(
        self,
        trading_days: list[date],
        prev_week_close_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Aggregate daily quotes into weekly summary.

        Args:
            trading_days: List of trading days in the week.
            prev_week_close_df: Previous week's closing prices for return calculation.

        Returns:
            DataFrame with weekly aggregated data.
        """
        if not trading_days:
            return pd.DataFrame()

        # Collect daily data
        daily_dfs = []
        for day in trading_days:
            date_str = day.strftime("%Y-%m-%d")
            df = self.cache.get(f"daily_quotes_{date_str}")

            if df is not None and not df.empty:
                df["TradeDate"] = day
                daily_dfs.append(df)
            elif self.fetcher:
                df = self.fetcher.fetch_daily_quotes(day)
                if not df.empty:
                    df["TradeDate"] = day
                    daily_dfs.append(df)

        if not daily_dfs:
            logger.warning("No daily data available for the week")
            return pd.DataFrame()

        # Combine all daily data
        combined_df = pd.concat(daily_dfs, ignore_index=True)

        # Sort by Code and Date
        combined_df = combined_df.sort_values(["Code", "TradeDate"])

        # Aggregate by Code
        weekly_agg = combined_df.groupby("Code").agg(
            WeekOpen=("Open", "first"),
            WeekHigh=("High", "max"),
            WeekLow=("Low", "min"),
            WeekClose=("Close", "last"),
            WeekVolume=("Volume", "sum"),
            WeekTurnover=("TurnoverValue", "sum"),
            TradingDays=("TradeDate", "nunique"),
            FirstDate=("TradeDate", "min"),
            LastDate=("TradeDate", "max"),
        ).reset_index()

        # Merge company info if available
        last_day_df = combined_df[combined_df["TradeDate"] == combined_df["TradeDate"].max()]
        info_cols = ["Code"]
        for col in ["CompanyName", "Sector33Code", "Sector33CodeName"]:
            if col in last_day_df.columns:
                info_cols.append(col)

        if len(info_cols) > 1:
            company_info = last_day_df[info_cols].drop_duplicates("Code")
            weekly_agg = weekly_agg.merge(company_info, on="Code", how="left")

        # Calculate weekly return if previous week data available
        if prev_week_close_df is not None and not prev_week_close_df.empty:
            prev_close = prev_week_close_df[["Code", "Close"]].rename(
                columns={"Close": "PrevWeekClose"}
            )
            weekly_agg = weekly_agg.merge(prev_close, on="Code", how="left")
            weekly_agg["WeeklyReturn"] = (
                (weekly_agg["WeekClose"] - weekly_agg["PrevWeekClose"])
                / weekly_agg["PrevWeekClose"]
                * 100
            )
        else:
            weekly_agg["WeeklyReturn"] = None
            weekly_agg["PrevWeekClose"] = None

        return weekly_agg

    def aggregate_indices(
        self,
        trading_days: list[date],
        prev_week_close_df: pd.DataFrame | None = None,
    ) -> pd.DataFrame:
        """Aggregate index data for the week.

        Args:
            trading_days: List of trading days in the week.
            prev_week_close_df: Previous week's index closing values.

        Returns:
            DataFrame with weekly index data.
        """
        if not trading_days:
            return pd.DataFrame()

        daily_dfs = []
        for day in trading_days:
            date_str = day.strftime("%Y-%m-%d")
            df = self.cache.get(f"indices_{date_str}")

            if df is not None and not df.empty:
                df["TradeDate"] = day
                daily_dfs.append(df)
            elif self.fetcher:
                df = self.fetcher.fetch_indices(day)
                if not df.empty:
                    df["TradeDate"] = day
                    daily_dfs.append(df)

        if not daily_dfs:
            return pd.DataFrame()

        combined_df = pd.concat(daily_dfs, ignore_index=True)
        combined_df = combined_df.sort_values(["Code", "TradeDate"])

        weekly_agg = combined_df.groupby("Code").agg(
            WeekOpen=("Open", "first"),
            WeekHigh=("High", "max"),
            WeekLow=("Low", "min"),
            WeekClose=("Close", "last"),
            FirstDate=("TradeDate", "min"),
            LastDate=("TradeDate", "max"),
        ).reset_index()

        if prev_week_close_df is not None and not prev_week_close_df.empty:
            prev_close = prev_week_close_df[["Code", "Close"]].rename(
                columns={"Close": "PrevWeekClose"}
            )
            weekly_agg = weekly_agg.merge(prev_close, on="Code", how="left")
            weekly_agg["WeeklyChange"] = weekly_agg["WeekClose"] - weekly_agg["PrevWeekClose"]
            weekly_agg["WeeklyChangeRate"] = (
                weekly_agg["WeeklyChange"] / weekly_agg["PrevWeekClose"] * 100
            )

        return weekly_agg

    def aggregate_sector_performance(
        self,
        weekly_quotes: pd.DataFrame,
    ) -> pd.DataFrame:
        """Aggregate sector performance from weekly stock data.

        Args:
            weekly_quotes: Weekly aggregated quote data with sector info.

        Returns:
            DataFrame with sector performance summary.
        """
        if weekly_quotes.empty or "Sector33CodeName" not in weekly_quotes.columns:
            return pd.DataFrame()

        # Filter out stocks without valid return data
        valid_data = weekly_quotes[weekly_quotes["WeeklyReturn"].notna()].copy()

        if valid_data.empty:
            return pd.DataFrame()

        sector_agg = valid_data.groupby(["Sector33Code", "Sector33CodeName"]).agg(
            AvgWeeklyReturn=("WeeklyReturn", "mean"),
            MedianWeeklyReturn=("WeeklyReturn", "median"),
            TotalTurnover=("WeekTurnover", "sum"),
            StockCount=("Code", "count"),
            AdvancingCount=("WeeklyReturn", lambda x: (x > 0).sum()),
            DecliningCount=("WeeklyReturn", lambda x: (x < 0).sum()),
        ).reset_index()

        # Sort by average return
        sector_agg = sector_agg.sort_values("AvgWeeklyReturn", ascending=False)

        return sector_agg

    def get_week_trades_spec(self, trading_days: list[date]) -> pd.DataFrame:
        """Get investor trading data for the week.

        Args:
            trading_days: List of trading days in the week.

        Returns:
            DataFrame with aggregated investor trading data.
        """
        if not trading_days:
            return pd.DataFrame()

        daily_dfs = []
        for day in trading_days:
            date_str = day.strftime("%Y-%m-%d")
            df = self.cache.get(f"trades_spec_{date_str}")

            if df is not None and not df.empty:
                df["TradeDate"] = day
                daily_dfs.append(df)
            elif self.fetcher:
                df = self.fetcher.fetch_trades_spec(day)
                if not df.empty:
                    df["TradeDate"] = day
                    daily_dfs.append(df)

        if not daily_dfs:
            return pd.DataFrame()

        return pd.concat(daily_dfs, ignore_index=True)

    def get_week_margin_data(self, week_end: date) -> pd.DataFrame:
        """Get margin trading data for the week.

        Note: Margin data is typically published weekly, so we use the
        week-end date to fetch the relevant data.

        Args:
            week_end: Week ending date.

        Returns:
            DataFrame with margin trading data.
        """
        date_str = week_end.strftime("%Y-%m-%d")
        df = self.cache.get(f"margin_interest_{date_str}")

        if df is not None:
            return df

        if self.fetcher:
            return self.fetcher.fetch_margin_interest(week_end)

        return pd.DataFrame()

    def get_historical_data(
        self,
        trading_days: list[date],
        lookback_weeks: int = 4,
    ) -> pd.DataFrame:
        """Get historical data for technical analysis.

        Args:
            trading_days: Current week's trading days.
            lookback_weeks: Number of weeks to look back.

        Returns:
            DataFrame with historical price data.
        """
        if not trading_days:
            return pd.DataFrame()

        # Calculate date range
        end_date = max(trading_days)
        start_date = end_date - timedelta(weeks=lookback_weeks)

        # Collect daily data
        all_data = []
        current_date = start_date

        while current_date <= end_date:
            if current_date.weekday() < 5:  # Weekday
                date_str = current_date.strftime("%Y-%m-%d")
                df = self.cache.get(f"daily_quotes_{date_str}")
                if df is not None and not df.empty:
                    if "Date" not in df.columns:
                        df["Date"] = date_str
                    all_data.append(df)
            current_date += timedelta(days=1)

        if not all_data:
            return pd.DataFrame()

        return pd.concat(all_data, ignore_index=True)
