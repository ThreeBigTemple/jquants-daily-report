"""Weekly technical analysis module.

Section 6: Technical Summary
- Advance-decline ratio
- New highs/lows
- Moving average analysis
- Market breadth indicators
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    MovingAverageStatus,
    TechnicalIndicatorData,
    WeeklyTechnicalSummary,
)

logger = logging.getLogger(__name__)


class WeeklyTechnicalAnalyzer:
    """Analyzer for weekly technical indicators (Section 6)."""

    def analyze(
        self,
        week_end: date,
        weekly_quotes: pd.DataFrame,
        historical_df: pd.DataFrame | None = None,
        prev_week_indicators: dict | None = None,
    ) -> WeeklyTechnicalSummary:
        """Analyze technical indicators for the week.

        Args:
            week_end: End date of the week.
            weekly_quotes: Weekly aggregated quote data.
            historical_df: Historical data for technical calculations.
            prev_week_indicators: Previous week's indicator values for comparison.

        Returns:
            WeeklyTechnicalSummary: Technical analysis summary.
        """
        # Calculate advance-decline ratio
        ad_ratio = self._calculate_advance_decline_ratio(weekly_quotes)

        # Calculate new highs/lows
        new_highs, new_lows = self._calculate_new_highs_lows(
            weekly_quotes,
            historical_df,
        )

        # Calculate moving average status
        moving_averages = self._calculate_ma_status(
            weekly_quotes,
            historical_df,
            prev_week_indicators,
        )

        # Build result
        ad_indicator = None
        if ad_ratio is not None:
            prev_ad = None
            ad_change = None
            if prev_week_indicators and "advance_decline_ratio" in prev_week_indicators:
                prev_ad = prev_week_indicators["advance_decline_ratio"]
                ad_change = ad_ratio - prev_ad

            signal = self._get_ad_signal(ad_ratio)
            ad_indicator = TechnicalIndicatorData(
                name="騰落レシオ",
                value=ad_ratio,
                prev_week_value=prev_ad,
                change=ad_change,
                signal=signal,
            )

        return WeeklyTechnicalSummary(
            week_end=week_end,
            advance_decline_ratio=ad_indicator,
            new_highs_count=new_highs,
            new_lows_count=new_lows,
            moving_averages=moving_averages,
        )

    def _calculate_advance_decline_ratio(
        self,
        weekly_quotes: pd.DataFrame,
    ) -> float | None:
        """Calculate advance-decline ratio for the week."""
        if weekly_quotes.empty or "WeeklyReturn" not in weekly_quotes.columns:
            return None

        valid_returns = weekly_quotes["WeeklyReturn"].dropna()
        if len(valid_returns) == 0:
            return None

        advancing = (valid_returns > 0).sum()
        declining = (valid_returns < 0).sum()

        if declining == 0:
            return None

        # Return as percentage
        ratio = (advancing / declining) * 100
        return float(ratio)

    def _calculate_new_highs_lows(
        self,
        weekly_quotes: pd.DataFrame,
        historical_df: pd.DataFrame | None,
        _period_weeks: int = 52,
    ) -> tuple[int, int]:
        """Calculate number of new highs and lows."""
        if weekly_quotes.empty:
            return 0, 0

        if historical_df is None or historical_df.empty:
            return 0, 0

        # Calculate period high/low for each stock
        if "High" not in historical_df.columns or "Low" not in historical_df.columns:
            return 0, 0

        # Group by Code and get high/low
        period_stats = historical_df.groupby("Code").agg(
            PeriodHigh=("High", "max"),
            PeriodLow=("Low", "min"),
        )

        # Merge with current week data
        merged = weekly_quotes.merge(
            period_stats,
            left_on="Code",
            right_index=True,
            how="left",
        )

        # Count new highs (weekly high >= period high)
        new_highs = 0
        new_lows = 0

        if "WeekHigh" in merged.columns and "PeriodHigh" in merged.columns:
            new_highs = int((merged["WeekHigh"] >= merged["PeriodHigh"]).sum())

        if "WeekLow" in merged.columns and "PeriodLow" in merged.columns:
            new_lows = int((merged["WeekLow"] <= merged["PeriodLow"]).sum())

        return new_highs, new_lows

    def _calculate_ma_status(
        self,
        weekly_quotes: pd.DataFrame,
        historical_df: pd.DataFrame | None,
        prev_week_indicators: dict | None,
    ) -> list[MovingAverageStatus]:
        """Calculate moving average status."""
        statuses = []

        if historical_df is None or historical_df.empty:
            return statuses

        if "Close" not in historical_df.columns:
            return statuses

        for period in [25, 75, 200]:
            # Calculate MA for each stock
            ma_values = historical_df.groupby("Code")["Close"].apply(
                lambda x, p=period: x.tail(p).mean() if len(x) >= p * 0.8 else None
            )

            if ma_values.empty:
                continue

            # Merge with weekly close
            merged = weekly_quotes.merge(
                ma_values.rename(f"MA{period}"),
                left_on="Code",
                right_index=True,
                how="left",
            )

            # Calculate percentage above MA
            valid_mask = merged[f"MA{period}"].notna()
            if not valid_mask.any():
                continue

            above_ma = (merged.loc[valid_mask, "WeekClose"] > merged.loc[valid_mask, f"MA{period}"]).sum()
            total = valid_mask.sum()

            stocks_above_pct = (above_ma / total) * 100 if total > 0 else 0

            # Get previous week value
            prev_pct = None
            if prev_week_indicators and f"ma{period}_pct" in prev_week_indicators:
                prev_pct = prev_week_indicators[f"ma{period}_pct"]

            # Determine trend
            trend = "横ばい"
            if prev_pct is not None:
                diff = stocks_above_pct - prev_pct
                if diff > 3:
                    trend = "上昇"
                elif diff < -3:
                    trend = "下落"

            statuses.append(
                MovingAverageStatus(
                    period=period,
                    stocks_above_pct=float(stocks_above_pct),
                    prev_week_pct=prev_pct,
                    trend=trend,
                )
            )

        return statuses

    def _get_ad_signal(self, ratio: float) -> str:
        """Get signal based on advance-decline ratio."""
        if ratio > 130:
            return "過熱（売りシグナル）"
        elif ratio > 120:
            return "買われ過ぎ"
        elif ratio > 80:
            return "中立"
        elif ratio > 70:
            return "売られ過ぎ"
        else:
            return "底入れ（買いシグナル）"
