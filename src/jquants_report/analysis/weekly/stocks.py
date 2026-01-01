"""Weekly stock analysis module.

Section 3: Performance Rankings
- Top gainers/losers
- Top volume/turnover
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    WeeklyPerformanceRankings,
    WeeklyStockPerformance,
)

logger = logging.getLogger(__name__)


class WeeklyStockAnalyzer:
    """Analyzer for weekly stock performance (Section 3)."""

    def analyze(
        self,
        week_end: date,
        weekly_quotes: pd.DataFrame,
        top_n: int = 10,
    ) -> WeeklyPerformanceRankings:
        """Analyze stock performance rankings for the week.

        Args:
            week_end: End date of the week.
            weekly_quotes: Aggregated weekly stock data.
            top_n: Number of top stocks to include in each ranking.

        Returns:
            WeeklyPerformanceRankings: Performance rankings.
        """
        top_gainers = self._get_top_gainers(weekly_quotes, top_n)
        top_losers = self._get_top_losers(weekly_quotes, top_n)
        top_volume = self._get_top_volume(weekly_quotes, top_n)
        top_turnover = self._get_top_turnover(weekly_quotes, top_n)

        return WeeklyPerformanceRankings(
            week_end=week_end,
            top_gainers=top_gainers,
            top_losers=top_losers,
            top_volume=top_volume,
            top_turnover=top_turnover,
        )

    def _convert_to_performance(self, row: pd.Series) -> WeeklyStockPerformance:
        """Convert a DataFrame row to WeeklyStockPerformance."""
        code = str(row.get("Code", ""))
        # Normalize 5-digit codes to 4-digit
        if len(code) == 5 and code.endswith("0"):
            code = code[:4]

        return WeeklyStockPerformance(
            code=code,
            name=str(row.get("CompanyName", "不明")),
            sector_name=str(row.get("Sector33CodeName", "不明")),
            week_open=float(row.get("WeekOpen", 0)),
            week_close=float(row.get("WeekClose", 0)),
            weekly_return_pct=float(row.get("WeeklyReturn", 0)) if pd.notna(row.get("WeeklyReturn")) else 0.0,
            week_volume=int(row.get("WeekVolume", 0)),
            week_turnover=float(row.get("WeekTurnover", 0)),
            week_high=float(row.get("WeekHigh", 0)) if pd.notna(row.get("WeekHigh")) else None,
            week_low=float(row.get("WeekLow", 0)) if pd.notna(row.get("WeekLow")) else None,
            prev_week_close=float(row.get("PrevWeekClose", 0)) if pd.notna(row.get("PrevWeekClose")) else None,
        )

    def _get_top_gainers(
        self,
        weekly_quotes: pd.DataFrame,
        top_n: int,
    ) -> list[WeeklyStockPerformance]:
        """Get top gaining stocks."""
        if weekly_quotes.empty or "WeeklyReturn" not in weekly_quotes.columns:
            return []

        valid_data = weekly_quotes[weekly_quotes["WeeklyReturn"].notna()].copy()
        sorted_data = valid_data.sort_values("WeeklyReturn", ascending=False).head(top_n)

        return [self._convert_to_performance(row) for _, row in sorted_data.iterrows()]

    def _get_top_losers(
        self,
        weekly_quotes: pd.DataFrame,
        top_n: int,
    ) -> list[WeeklyStockPerformance]:
        """Get top losing stocks."""
        if weekly_quotes.empty or "WeeklyReturn" not in weekly_quotes.columns:
            return []

        valid_data = weekly_quotes[weekly_quotes["WeeklyReturn"].notna()].copy()
        sorted_data = valid_data.sort_values("WeeklyReturn", ascending=True).head(top_n)

        return [self._convert_to_performance(row) for _, row in sorted_data.iterrows()]

    def _get_top_volume(
        self,
        weekly_quotes: pd.DataFrame,
        top_n: int,
    ) -> list[WeeklyStockPerformance]:
        """Get top volume stocks."""
        if weekly_quotes.empty or "WeekVolume" not in weekly_quotes.columns:
            return []

        sorted_data = weekly_quotes.sort_values("WeekVolume", ascending=False).head(top_n)

        return [self._convert_to_performance(row) for _, row in sorted_data.iterrows()]

    def _get_top_turnover(
        self,
        weekly_quotes: pd.DataFrame,
        top_n: int,
    ) -> list[WeeklyStockPerformance]:
        """Get top turnover stocks."""
        if weekly_quotes.empty or "WeekTurnover" not in weekly_quotes.columns:
            return []

        sorted_data = weekly_quotes.sort_values("WeekTurnover", ascending=False).head(top_n)

        return [self._convert_to_performance(row) for _, row in sorted_data.iterrows()]
