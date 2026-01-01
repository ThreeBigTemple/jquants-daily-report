"""Weekly topics analysis module.

Section 8: Weekly Topics
- Notable market topics
- Price movement highlights
- Sector highlights
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    MarketTopic,
    PriceMovementHighlight,
    WeeklyTopics,
)

logger = logging.getLogger(__name__)


class WeeklyTopicsAnalyzer:
    """Analyzer for weekly topics and highlights (Section 8)."""

    # Thresholds for notable movements
    NOTABLE_GAIN_PCT = 20.0  # 20% gain is notable
    NOTABLE_LOSS_PCT = -20.0  # 20% loss is notable

    def analyze(
        self,
        week_end: date,
        weekly_quotes: pd.DataFrame,
        sector_performance: pd.DataFrame | None = None,
        historical_df: pd.DataFrame | None = None,
    ) -> WeeklyTopics:
        """Analyze weekly topics and highlights.

        Args:
            week_end: End date of the week.
            weekly_quotes: Weekly aggregated quote data.
            sector_performance: Sector performance data.
            historical_df: Historical data for comparison.

        Returns:
            WeeklyTopics: Topics and highlights analysis.
        """
        # Find notable movers (大幅上昇/下落) separately from year high/low
        price_highlights = self._find_notable_movers(weekly_quotes)
        year_high_low_stocks = self._find_year_high_low(weekly_quotes, historical_df)
        sector_highlights = self._find_sector_highlights(sector_performance)

        # Combine for market topics generation
        all_highlights = price_highlights + year_high_low_stocks
        market_topics = self._generate_market_topics(
            weekly_quotes,
            sector_performance,
            all_highlights,
        )

        return WeeklyTopics(
            week_end=week_end,
            market_topics=market_topics,
            price_highlights=price_highlights,
            year_high_low_stocks=year_high_low_stocks,
            sector_highlights=sector_highlights,
        )

    def _find_notable_movers(
        self,
        weekly_quotes: pd.DataFrame,
    ) -> list[PriceMovementHighlight]:
        """Find stocks with notable price movements (大幅上昇/大幅下落).

        Args:
            weekly_quotes: Weekly quote data.

        Returns:
            List of notable movers.
        """
        highlights: list[PriceMovementHighlight] = []
        seen_codes: set[str] = set()

        if weekly_quotes.empty or "WeeklyReturn" not in weekly_quotes.columns:
            return highlights

        for _, row in weekly_quotes.iterrows():
            ret = row.get("WeeklyReturn")
            if pd.isna(ret):
                continue

            code = str(row.get("Code", ""))
            if len(code) == 5 and code.endswith("0"):
                code = code[:4]

            name = str(row.get("CompanyName", "不明"))
            price = float(row.get("WeekClose", 0))

            movement_type = None
            if ret >= self.NOTABLE_GAIN_PCT:
                movement_type = "大幅上昇"
            elif ret <= self.NOTABLE_LOSS_PCT:
                movement_type = "大幅下落"

            if movement_type and code not in seen_codes:
                highlights.append(
                    PriceMovementHighlight(
                        code=code,
                        name=name,
                        movement_type=movement_type,
                        price=price,
                        change_pct=float(ret),
                    )
                )
                seen_codes.add(code)

        # Sort by absolute return (most significant first)
        highlights.sort(key=lambda x: abs(x.change_pct), reverse=True)

        return highlights[:20]

    def _find_year_high_low(
        self,
        weekly_quotes: pd.DataFrame,
        historical_df: pd.DataFrame | None,
    ) -> list[PriceMovementHighlight]:
        """Find stocks at year-to-date highs or lows.

        Args:
            weekly_quotes: Weekly quote data.
            historical_df: Historical data for comparison.

        Returns:
            List of stocks at year highs/lows.
        """
        highlights: list[PriceMovementHighlight] = []
        seen_codes: set[str] = set()

        if historical_df is None or historical_df.empty:
            return highlights

        if "High" not in historical_df.columns or "Low" not in historical_df.columns:
            return highlights

        # Calculate year-to-date high/low
        year_stats = historical_df.groupby("Code").agg(
            YearHigh=("High", "max"),
            YearLow=("Low", "min"),
        )

        merged = weekly_quotes.merge(
            year_stats,
            left_on="Code",
            right_index=True,
            how="left",
        )

        for _, row in merged.iterrows():
            code = str(row.get("Code", ""))
            if len(code) == 5 and code.endswith("0"):
                code = code[:4]

            if code in seen_codes:
                continue

            week_high = row.get("WeekHigh")
            week_low = row.get("WeekLow")
            year_high = row.get("YearHigh")
            year_low = row.get("YearLow")

            weekly_return = row.get("WeeklyReturn")
            change_pct = float(weekly_return) if pd.notna(weekly_return) else 0.0

            if pd.notna(week_high) and pd.notna(year_high) and week_high >= year_high:
                highlights.append(
                    PriceMovementHighlight(
                        code=code,
                        name=str(row.get("CompanyName", "不明")),
                        movement_type="年初来高値",
                        price=float(week_high),
                        change_pct=change_pct,
                    )
                )
                seen_codes.add(code)
            elif pd.notna(week_low) and pd.notna(year_low) and week_low <= year_low:
                highlights.append(
                    PriceMovementHighlight(
                        code=code,
                        name=str(row.get("CompanyName", "不明")),
                        movement_type="年初来安値",
                        price=float(week_low),
                        change_pct=change_pct,
                    )
                )
                seen_codes.add(code)

        # Sort by absolute return
        highlights.sort(key=lambda x: abs(x.change_pct), reverse=True)

        return highlights[:20]

    def _find_sector_highlights(
        self,
        sector_performance: pd.DataFrame | None,
    ) -> list[str]:
        """Find notable sector movements."""
        highlights = []

        if sector_performance is None or sector_performance.empty:
            return highlights

        # Top 3 sectors
        top_sectors = sector_performance.nlargest(3, "AvgWeeklyReturn")
        for _, row in top_sectors.iterrows():
            name = str(row.get("Sector33CodeName", "不明"))
            ret = float(row.get("AvgWeeklyReturn", 0))
            highlights.append(f"{name}セクターが+{ret:.1f}%と好調")

        # Bottom 3 sectors
        bottom_sectors = sector_performance.nsmallest(3, "AvgWeeklyReturn")
        for _, row in bottom_sectors.iterrows():
            name = str(row.get("Sector33CodeName", "不明"))
            ret = float(row.get("AvgWeeklyReturn", 0))
            highlights.append(f"{name}セクターが{ret:.1f}%と軟調")

        return highlights

    def _generate_market_topics(
        self,
        weekly_quotes: pd.DataFrame,
        sector_performance: pd.DataFrame | None,
        price_highlights: list[PriceMovementHighlight],
    ) -> list[MarketTopic]:
        """Generate market topic summaries."""
        topics = []

        if weekly_quotes.empty:
            return topics

        # Analyze overall market trend
        valid_returns = weekly_quotes["WeeklyReturn"].dropna()
        if len(valid_returns) > 0:
            avg_return = valid_returns.mean()
            advancing = (valid_returns > 0).sum()
            declining = (valid_returns < 0).sum()
            total = len(valid_returns)

            if avg_return > 1:
                impact = "ポジティブ"
                title = "週間相場は上昇基調"
                desc = f"全体の{advancing/total*100:.1f}%が値上がり、平均騰落率は+{avg_return:.1f}%"
            elif avg_return < -1:
                impact = "ネガティブ"
                title = "週間相場は下落基調"
                desc = f"全体の{declining/total*100:.1f}%が値下がり、平均騰落率は{avg_return:.1f}%"
            else:
                impact = "中立"
                title = "週間相場は横ばい"
                desc = f"値上がり{advancing/total*100:.1f}%、値下がり{declining/total*100:.1f}%と拮抗"

            topics.append(
                MarketTopic(
                    title=title,
                    description=desc,
                    impact=impact,
                )
            )

        # Sector rotation topic
        if sector_performance is not None and not sector_performance.empty:
            top_sector = sector_performance.nlargest(1, "AvgWeeklyReturn").iloc[0]
            bottom_sector = sector_performance.nsmallest(1, "AvgWeeklyReturn").iloc[0]

            top_ret = float(top_sector.get("AvgWeeklyReturn", 0))
            bottom_ret = float(bottom_sector.get("AvgWeeklyReturn", 0))
            spread = top_ret - bottom_ret

            if spread > 5:
                topics.append(
                    MarketTopic(
                        title="セクター間格差が拡大",
                        description=f"トップ{top_sector['Sector33CodeName']}と"
                        f"ボトム{bottom_sector['Sector33CodeName']}で{spread:.1f}%の差",
                        impact="中立",
                    )
                )

        # Notable movers topic
        if len(price_highlights) >= 5:
            gainers = [h for h in price_highlights if h.change_pct > 0]
            losers = [h for h in price_highlights if h.change_pct < 0]

            if len(gainers) > len(losers) * 2:
                topics.append(
                    MarketTopic(
                        title="大幅上昇銘柄が目立つ",
                        description=f"{len(gainers)}銘柄が20%以上の上昇",
                        related_codes=[h.code for h in gainers[:5]],
                        impact="ポジティブ",
                    )
                )
            elif len(losers) > len(gainers) * 2:
                topics.append(
                    MarketTopic(
                        title="急落銘柄に警戒",
                        description=f"{len(losers)}銘柄が20%以上の下落",
                        related_codes=[h.code for h in losers[:5]],
                        impact="ネガティブ",
                    )
                )

        return topics
