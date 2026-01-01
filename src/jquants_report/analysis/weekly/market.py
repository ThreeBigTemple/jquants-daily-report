"""Weekly market analysis module.

Section 1: Weekly Market Summary
- Index performance (TOPIX, Nikkei 225)
- Daily changes throughout the week
- Advancing/declining stock counts
- Volume and turnover statistics
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    DailyIndexChange,
    WeeklyIndexData,
    WeeklyMarketSummary,
)

logger = logging.getLogger(__name__)


class WeeklyMarketAnalyzer:
    """Analyzer for weekly market summary (Section 1)."""

    # Index codes for J-Quants API
    INDEX_CODES = {
        "0000": "TOPIX",
        "0001": "日経225",
    }

    def analyze(
        self,
        week_start: date,
        week_end: date,
        weekly_indices: pd.DataFrame,
        weekly_quotes: pd.DataFrame,
        daily_indices_list: list[tuple[date, pd.DataFrame]],
    ) -> WeeklyMarketSummary:
        """Analyze weekly market data.

        Args:
            week_start: Start date of the week.
            week_end: End date of the week.
            weekly_indices: Aggregated weekly index data.
            weekly_quotes: Aggregated weekly stock data.
            daily_indices_list: List of (date, DataFrame) tuples for daily indices.

        Returns:
            WeeklyMarketSummary: Complete weekly market summary.
        """
        # Process index data
        indices = self._process_indices(weekly_indices)

        # Process daily changes
        daily_changes = self._process_daily_changes(daily_indices_list)

        # Calculate market breadth
        advancing, declining, unchanged = self._calculate_breadth(weekly_quotes)

        # Calculate volume and turnover
        total_volume, total_turnover = self._calculate_volume_turnover(weekly_quotes)

        return WeeklyMarketSummary(
            week_start=week_start,
            week_end=week_end,
            indices=indices,
            daily_changes=daily_changes,
            total_advancing=advancing,
            total_declining=declining,
            total_unchanged=unchanged,
            week_total_volume=total_volume,
            week_total_turnover=total_turnover,
        )

    def _process_indices(self, weekly_indices: pd.DataFrame) -> list[WeeklyIndexData]:
        """Process weekly index data."""
        indices = []

        if weekly_indices.empty:
            return indices

        for code, name in self.INDEX_CODES.items():
            row = weekly_indices[weekly_indices["Code"] == code]
            if row.empty:
                continue

            row = row.iloc[0]
            weekly_change = row.get("WeeklyChange", 0.0)
            weekly_change_rate = row.get("WeeklyChangeRate", 0.0)

            indices.append(
                WeeklyIndexData(
                    name=name,
                    week_open=float(row.get("WeekOpen", 0)),
                    week_high=float(row.get("WeekHigh", 0)),
                    week_low=float(row.get("WeekLow", 0)),
                    week_close=float(row.get("WeekClose", 0)),
                    weekly_change=float(weekly_change) if pd.notna(weekly_change) else 0.0,
                    weekly_change_pct=float(weekly_change_rate) if pd.notna(weekly_change_rate) else 0.0,
                )
            )

        return indices

    def _process_daily_changes(
        self,
        daily_indices_list: list[tuple[date, pd.DataFrame]],
    ) -> dict[str, list[DailyIndexChange]]:
        """Process daily index changes."""
        daily_changes: dict[str, list[DailyIndexChange]] = {}

        for index_name in self.INDEX_CODES.values():
            daily_changes[index_name] = []

        prev_closes: dict[str, float] = {}

        for day, df in sorted(daily_indices_list, key=lambda x: x[0]):
            if df.empty:
                continue

            for code, name in self.INDEX_CODES.items():
                row = df[df["Code"] == code]
                if row.empty:
                    continue

                close = float(row.iloc[0].get("Close", 0))
                prev_close = prev_closes.get(name)

                if prev_close is not None:
                    change = close - prev_close
                    change_pct = (change / prev_close) * 100 if prev_close != 0 else 0
                else:
                    change = 0.0
                    change_pct = 0.0

                daily_changes[name].append(
                    DailyIndexChange(
                        date=day,
                        close=close,
                        change=change,
                        change_pct=change_pct,
                    )
                )

                prev_closes[name] = close

        return daily_changes

    def _calculate_breadth(
        self,
        weekly_quotes: pd.DataFrame,
    ) -> tuple[int, int, int]:
        """Calculate market breadth (advancing/declining/unchanged)."""
        if weekly_quotes.empty or "WeeklyReturn" not in weekly_quotes.columns:
            return 0, 0, 0

        valid_returns = weekly_quotes["WeeklyReturn"].dropna()

        advancing = int((valid_returns > 0).sum())
        declining = int((valid_returns < 0).sum())
        unchanged = int((valid_returns == 0).sum())

        return advancing, declining, unchanged

    def _calculate_volume_turnover(
        self,
        weekly_quotes: pd.DataFrame,
    ) -> tuple[float, float]:
        """Calculate total volume and turnover for the week."""
        if weekly_quotes.empty:
            return 0.0, 0.0

        total_volume = float(weekly_quotes.get("WeekVolume", pd.Series([0])).sum())
        total_turnover = float(weekly_quotes.get("WeekTurnover", pd.Series([0])).sum())

        return total_volume, total_turnover
