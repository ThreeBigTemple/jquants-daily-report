"""Weekly trends analysis module.

Section 9: Medium-term Trend Check
- 1-week, 1-month, 3-month trends
- Index trend analysis
- Sector trend analysis
- Outlook summary
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    SectorTrendData,
    TrendData,
    WeeklyMediumTermTrends,
)

logger = logging.getLogger(__name__)


class WeeklyTrendsAnalyzer:
    """Analyzer for medium-term trend confirmation (Section 9)."""

    # Index codes
    INDEX_CODES = {
        "0000": "TOPIX",
        "0001": "日経225",
    }

    def analyze(
        self,
        week_end: date,
        weekly_indices: pd.DataFrame,
        weekly_quotes: pd.DataFrame,
        historical_indices: list[tuple[date, pd.DataFrame]],
        historical_sector_perf: list[tuple[date, pd.DataFrame]],
    ) -> WeeklyMediumTermTrends:
        """Analyze medium-term trends.

        Args:
            week_end: End date of the week.
            weekly_indices: Current week's index data.
            weekly_quotes: Current week's stock data.
            historical_indices: Historical index data by week.
            historical_sector_perf: Historical sector performance by week.

        Returns:
            WeeklyMediumTermTrends: Trend analysis.
        """
        index_trends = self._calculate_index_trends(
            week_end,
            weekly_indices,
            historical_indices,
        )

        sector_trends = self._calculate_sector_trends(
            week_end,
            weekly_quotes,
            historical_sector_perf,
        )

        market_breadth_trend = self._assess_market_breadth(weekly_quotes)
        outlook_summary = self._generate_outlook(
            index_trends,
            sector_trends,
            market_breadth_trend,
        )

        return WeeklyMediumTermTrends(
            week_end=week_end,
            index_trends=index_trends,
            sector_trends=sector_trends,
            market_breadth_trend=market_breadth_trend,
            outlook_summary=outlook_summary,
        )

    def _calculate_index_trends(
        self,
        _week_end: date,
        weekly_indices: pd.DataFrame,
        historical_indices: list[tuple[date, pd.DataFrame]],
    ) -> dict[str, list[TrendData]]:
        """Calculate index trends for different periods."""
        trends: dict[str, list[TrendData]] = {}

        if weekly_indices.empty:
            return trends

        # Sort historical data by date
        sorted_history = sorted(historical_indices, key=lambda x: x[0], reverse=True)

        for code, name in self.INDEX_CODES.items():
            trends[name] = []

            current_row = weekly_indices[weekly_indices["Code"] == code]
            if current_row.empty:
                continue

            current_close = float(current_row.iloc[0].get("WeekClose", 0))
            if current_close == 0:
                continue

            # 1 week ago
            one_week_ago = self._find_historical_value(sorted_history, code, 1)
            if one_week_ago:
                trends[name].append(
                    self._create_trend_data("1週間", one_week_ago, current_close)
                )

            # 4 weeks ago (approx 1 month)
            four_weeks_ago = self._find_historical_value(sorted_history, code, 4)
            if four_weeks_ago:
                trends[name].append(
                    self._create_trend_data("1ヶ月", four_weeks_ago, current_close)
                )

            # 13 weeks ago (approx 3 months)
            thirteen_weeks_ago = self._find_historical_value(sorted_history, code, 13)
            if thirteen_weeks_ago:
                trends[name].append(
                    self._create_trend_data("3ヶ月", thirteen_weeks_ago, current_close)
                )

        return trends

    def _find_historical_value(
        self,
        sorted_history: list[tuple[date, pd.DataFrame]],
        code: str,
        weeks_ago: int,
    ) -> float | None:
        """Find historical close value for an index."""
        if weeks_ago > len(sorted_history):
            return None

        if weeks_ago == 0:
            return None

        # Get data from weeks_ago
        idx = weeks_ago - 1
        if idx >= len(sorted_history):
            return None

        _, hist_df = sorted_history[idx]
        if hist_df.empty:
            return None

        row = hist_df[hist_df["Code"] == code]
        if row.empty:
            return None

        close = row.iloc[0].get("Close", row.iloc[0].get("WeekClose", 0))
        return float(close) if pd.notna(close) else None

    def _create_trend_data(
        self,
        period_name: str,
        start_value: float,
        end_value: float,
    ) -> TrendData:
        """Create TrendData from start and end values."""
        change = end_value - start_value
        change_pct = (change / start_value) * 100 if start_value != 0 else 0

        if change_pct > 2:
            direction = "上昇"
        elif change_pct < -2:
            direction = "下落"
        else:
            direction = "横ばい"

        return TrendData(
            period_name=period_name,
            start_value=start_value,
            end_value=end_value,
            change=change,
            change_pct=change_pct,
            trend_direction=direction,
        )

    def _calculate_sector_trends(
        self,
        _week_end: date,
        weekly_quotes: pd.DataFrame,
        historical_sector_perf: list[tuple[date, pd.DataFrame]],
    ) -> list[SectorTrendData]:
        """Calculate sector trends."""
        sector_trends = []

        if weekly_quotes.empty or "Sector33CodeName" not in weekly_quotes.columns:
            return sector_trends

        # Current week sector performance
        current_sector = weekly_quotes.groupby("Sector33CodeName").agg(
            OneWeekReturn=("WeeklyReturn", "mean"),
        ).reset_index()

        # Historical sector performance
        sorted_history = sorted(historical_sector_perf, key=lambda x: x[0], reverse=True)

        for _, row in current_sector.iterrows():
            sector_name = str(row.get("Sector33CodeName", ""))
            one_week = float(row.get("OneWeekReturn", 0))

            one_month = None
            three_month = None

            # Look for historical data
            if len(sorted_history) >= 4:
                one_month = self._find_sector_historical_return(
                    sorted_history, sector_name, 0, 4
                )

            if len(sorted_history) >= 13:
                three_month = self._find_sector_historical_return(
                    sorted_history, sector_name, 0, 13
                )

            # Determine trend strength
            trend_strength = "中立"
            if one_week > 0 and (one_month is None or one_month > 0):
                trend_strength = "強気"
            elif one_week < 0 and (one_month is None or one_month < 0):
                trend_strength = "弱気"

            sector_trends.append(
                SectorTrendData(
                    sector_name=sector_name,
                    one_week_return=one_week,
                    one_month_return=one_month,
                    three_month_return=three_month,
                    trend_strength=trend_strength,
                )
            )

        # Sort by one-week return
        sector_trends.sort(key=lambda x: x.one_week_return, reverse=True)

        return sector_trends

    def _find_sector_historical_return(
        self,
        sorted_history: list[tuple[date, pd.DataFrame]],
        sector_name: str,
        start_idx: int,
        end_idx: int,
    ) -> float | None:
        """Calculate cumulative return for a sector over a period."""
        if end_idx > len(sorted_history):
            return None

        cumulative_return = 0.0
        found_data = False

        for i in range(start_idx, end_idx):
            if i >= len(sorted_history):
                break

            _, hist_df = sorted_history[i]
            if hist_df.empty:
                continue

            row = hist_df[hist_df["Sector33CodeName"] == sector_name]
            if row.empty:
                continue

            ret = row.iloc[0].get("AvgWeeklyReturn")
            if pd.notna(ret):
                cumulative_return += float(ret)
                found_data = True

        return cumulative_return if found_data else None

    def _assess_market_breadth(self, weekly_quotes: pd.DataFrame) -> str:
        """Assess overall market breadth trend."""
        if weekly_quotes.empty or "WeeklyReturn" not in weekly_quotes.columns:
            return "中立"

        valid_returns = weekly_quotes["WeeklyReturn"].dropna()
        if len(valid_returns) == 0:
            return "中立"

        avg_return = valid_returns.mean()
        advancing_pct = (valid_returns > 0).sum() / len(valid_returns) * 100

        if advancing_pct > 60 and avg_return > 1:
            return "強気"
        elif advancing_pct < 40 and avg_return < -1:
            return "弱気"
        else:
            return "中立"

    def _generate_outlook(
        self,
        index_trends: dict[str, list[TrendData]],
        sector_trends: list[SectorTrendData],
        market_breadth: str,
    ) -> str:
        """Generate outlook summary."""
        outlook_parts = []

        # Index trend summary
        for name, trends in index_trends.items():
            if trends:
                latest = trends[0]  # 1-week trend
                if latest.trend_direction == "上昇":
                    outlook_parts.append(f"{name}は上昇基調を維持")
                elif latest.trend_direction == "下落":
                    outlook_parts.append(f"{name}は下落傾向")
                else:
                    outlook_parts.append(f"{name}は横ばい推移")

        # Sector trend summary
        if sector_trends:
            strong_sectors = [s for s in sector_trends if s.trend_strength == "強気"]
            weak_sectors = [s for s in sector_trends if s.trend_strength == "弱気"]

            if len(strong_sectors) > len(weak_sectors):
                outlook_parts.append("セクター全体では強気優勢")
            elif len(weak_sectors) > len(strong_sectors):
                outlook_parts.append("セクター全体では弱気優勢")

        # Market breadth
        if market_breadth == "強気":
            outlook_parts.append("市場全体の騰落状況は良好")
        elif market_breadth == "弱気":
            outlook_parts.append("市場全体は軟調な展開")

        return "。".join(outlook_parts) + "。" if outlook_parts else "市場は様子見の展開。"
