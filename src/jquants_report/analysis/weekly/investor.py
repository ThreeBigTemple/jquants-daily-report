"""Weekly investor trading analysis module.

Section 4: Investor Trading Activity
- Foreign investors
- Individual investors
- Institutional investors
- Securities companies
"""

import logging
from datetime import date

import pandas as pd

from jquants_report.report.weekly_types import (
    InvestorCategory,
    WeeklyInvestorActivity,
)

logger = logging.getLogger(__name__)


class WeeklyInvestorAnalyzer:
    """Analyzer for weekly investor trading activity (Section 4)."""

    # Investor type mappings (based on J-Quants API)
    INVESTOR_TYPES = {
        "Proprietary": "自己売買",
        "Brokerage": "委託取引",
        "Total": "合計",
        "Foreigners": "外国人",
        "Individuals": "個人",
        "InstitutionalTotal": "機関投資家計",
        "Trust": "信託銀行",
        "InsurancePension": "生損保等",
        "OtherCorps": "その他法人",
        "Securities": "証券会社",
    }

    def analyze(
        self,
        week_end: date,
        trades_spec_df: pd.DataFrame,
        prev_week_trades_spec_df: pd.DataFrame | None = None,
    ) -> WeeklyInvestorActivity:
        """Analyze investor trading activity.

        Args:
            week_end: End date of the week.
            trades_spec_df: Trading by investor type data for the week.
            prev_week_trades_spec_df: Previous week's data for comparison.

        Returns:
            WeeklyInvestorActivity: Investor activity analysis.
        """
        categories = self._process_categories(
            trades_spec_df,
            prev_week_trades_spec_df,
        )

        # Extract key metrics
        foreigners_net = self._get_net_for_type(categories, "外国人")
        individuals_net = self._get_net_for_type(categories, "個人")
        institutions_net = self._get_net_for_type(categories, "機関投資家計")

        return WeeklyInvestorActivity(
            week_end=week_end,
            categories=categories,
            foreigners_net=foreigners_net,
            individuals_net=individuals_net,
            institutions_net=institutions_net,
        )

    def _process_categories(
        self,
        trades_spec_df: pd.DataFrame,
        prev_week_df: pd.DataFrame | None,
    ) -> list[InvestorCategory]:
        """Process investor category data."""
        categories = []

        if trades_spec_df.empty:
            return categories

        # Aggregate weekly data
        weekly_totals = self._aggregate_weekly_data(trades_spec_df)

        # Aggregate previous week data
        prev_week_totals = None
        if prev_week_df is not None and not prev_week_df.empty:
            prev_week_totals = self._aggregate_weekly_data(prev_week_df)

        for category_type, display_name in self.INVESTOR_TYPES.items():
            buy_col = f"{category_type}BuyValue"
            sell_col = f"{category_type}SellValue"

            if buy_col not in weekly_totals or sell_col not in weekly_totals:
                continue

            buy_value = weekly_totals.get(buy_col, 0)
            sell_value = weekly_totals.get(sell_col, 0)
            net_value = buy_value - sell_value

            prev_week_net = None
            net_change = None
            if prev_week_totals is not None:
                prev_buy = prev_week_totals.get(buy_col, 0)
                prev_sell = prev_week_totals.get(sell_col, 0)
                prev_week_net = prev_buy - prev_sell
                net_change = net_value - prev_week_net

            categories.append(
                InvestorCategory(
                    category_name=display_name,
                    buy_value=buy_value,
                    sell_value=sell_value,
                    net_value=net_value,
                    prev_week_net=prev_week_net,
                    net_change=net_change,
                )
            )

        return categories

    def _aggregate_weekly_data(self, df: pd.DataFrame) -> dict:
        """Aggregate trading data for a week."""
        # Sum all numeric columns
        numeric_cols = df.select_dtypes(include=["number"]).columns
        return df[numeric_cols].sum().to_dict()

    def _get_net_for_type(
        self,
        categories: list[InvestorCategory],
        type_name: str,
    ) -> float:
        """Get net value for a specific investor type."""
        for cat in categories:
            if cat.category_name == type_name:
                return cat.net_value
        return 0.0
