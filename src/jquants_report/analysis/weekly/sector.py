"""Weekly sector analysis module.

Section 2: Sector Rotation
- Top/bottom performing sectors
- Week-over-week comparison
- Sector turnover analysis
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    SectorRotationData,
    WeeklySectorRotation,
)

logger = logging.getLogger(__name__)


class WeeklySectorAnalyzer:
    """Analyzer for weekly sector rotation (Section 2)."""

    def analyze(
        self,
        week_end: date,
        sector_performance: pd.DataFrame,
        prev_week_sector_performance: pd.DataFrame | None = None,
    ) -> WeeklySectorRotation:
        """Analyze sector rotation for the week.

        Args:
            week_end: End date of the week.
            sector_performance: Current week's sector performance.
            prev_week_sector_performance: Previous week's sector performance.

        Returns:
            WeeklySectorRotation: Sector rotation analysis.
        """
        all_sectors = self._process_sectors(
            sector_performance,
            prev_week_sector_performance,
        )

        # Sort by return
        sorted_sectors = sorted(all_sectors, key=lambda x: x.weekly_return_pct, reverse=True)

        # Top 5 and bottom 5
        top_sectors = sorted_sectors[:5]
        bottom_sectors = sorted_sectors[-5:][::-1]  # Reverse to show worst first

        return WeeklySectorRotation(
            week_end=week_end,
            top_sectors=top_sectors,
            bottom_sectors=bottom_sectors,
            all_sectors=sorted_sectors,
        )

    def _process_sectors(
        self,
        sector_performance: pd.DataFrame,
        prev_week_performance: pd.DataFrame | None,
    ) -> list[SectorRotationData]:
        """Process sector performance data."""
        sectors = []

        if sector_performance.empty:
            return sectors

        # Create lookup for previous week
        prev_week_lookup: dict[str, float] = {}
        if prev_week_performance is not None and not prev_week_performance.empty:
            for _, row in prev_week_performance.iterrows():
                code = str(row.get("Sector33Code", ""))
                ret = row.get("AvgWeeklyReturn")
                if code and pd.notna(ret):
                    prev_week_lookup[code] = float(ret)

        for _, row in sector_performance.iterrows():
            sector_code = str(row.get("Sector33Code", ""))
            sector_name = str(row.get("Sector33CodeName", "不明"))
            weekly_return = float(row.get("AvgWeeklyReturn", 0))

            prev_week_return = prev_week_lookup.get(sector_code)
            return_change = None
            if prev_week_return is not None:
                return_change = weekly_return - prev_week_return

            sectors.append(
                SectorRotationData(
                    sector_code=sector_code,
                    sector_name=sector_name,
                    weekly_return_pct=weekly_return,
                    prev_week_return_pct=prev_week_return,
                    return_change=return_change,
                    turnover=float(row.get("TotalTurnover", 0)),
                    stock_count=int(row.get("StockCount", 0)),
                    advancing_count=int(row.get("AdvancingCount", 0)),
                    declining_count=int(row.get("DecliningCount", 0)),
                )
            )

        return sectors
