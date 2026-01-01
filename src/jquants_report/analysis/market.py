"""Market overview analysis module.

This module provides functionality to analyze overall market conditions including
major indices, advancing/declining issues, and trading volume.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class MarketOverview:
    """Market overview analysis results.

    Attributes:
        date: Analysis date.
        topix_close: TOPIX closing value.
        topix_change: TOPIX change from previous day.
        topix_change_pct: TOPIX percentage change.
        nikkei225_close: Nikkei 225 closing value.
        nikkei225_change: Nikkei 225 change from previous day.
        nikkei225_change_pct: Nikkei 225 percentage change.
        advancing_issues: Number of advancing issues.
        declining_issues: Number of declining issues.
        unchanged_issues: Number of unchanged issues.
        total_issues: Total number of issues.
        total_volume: Total trading volume (shares).
        total_value: Total trading value (yen).
        average_change_pct: Average percentage change across all stocks.
    """

    date: str
    topix_close: float | None = None
    topix_change: float | None = None
    topix_change_pct: float | None = None
    nikkei225_close: float | None = None
    nikkei225_change: float | None = None
    nikkei225_change_pct: float | None = None
    advancing_issues: int = 0
    declining_issues: int = 0
    unchanged_issues: int = 0
    total_issues: int = 0
    total_volume: float = 0.0
    total_value: float = 0.0
    average_change_pct: float | None = None


class MarketAnalyzer:
    """Analyzer for overall market conditions."""

    def analyze(
        self,
        date: str,
        prices_df: pd.DataFrame,
        indices_df: pd.DataFrame | None = None,
    ) -> MarketOverview:
        """Analyze market overview for a given date.

        Args:
            date: Analysis date in YYYY-MM-DD format.
            prices_df: DataFrame containing stock price data with columns:
                - Code: Stock code
                - Close: Closing price
                - Volume: Trading volume
                - TurnoverValue: Trading value
                - ChangeRate: Change rate (percentage)
            indices_df: Optional DataFrame containing index data with columns:
                - Code: Index code (e.g., '0000' for TOPIX)
                - Close: Closing value
                - ChangeRate: Change rate (percentage)

        Returns:
            MarketOverview: Analysis results.
        """
        overview = MarketOverview(date=date)

        # Calculate advancing/declining issues
        if not prices_df.empty and "ChangeRate" in prices_df.columns:
            change_rates = prices_df["ChangeRate"].dropna()
            overview.advancing_issues = int((change_rates > 0).sum())
            overview.declining_issues = int((change_rates < 0).sum())
            overview.unchanged_issues = int((change_rates == 0).sum())
            overview.total_issues = len(change_rates)
            overview.average_change_pct = float(change_rates.mean())

        # Calculate total volume and value
        if not prices_df.empty:
            if "Volume" in prices_df.columns:
                overview.total_volume = float(prices_df["Volume"].sum())
            if "TurnoverValue" in prices_df.columns:
                overview.total_value = float(prices_df["TurnoverValue"].sum())

        # Extract index data if available
        if indices_df is not None and not indices_df.empty:
            # Ensure Code column is string type for comparison
            indices_df = indices_df.copy()
            indices_df["Code"] = indices_df["Code"].astype(str)

            # TOPIX (code: 0000 or TOPIX in name)
            topix = indices_df[
                (indices_df["Code"] == "0000") |
                (indices_df["Code"].str.contains("0000", na=False)) |
                (indices_df.get("IndexName", pd.Series()).str.contains("TOPIX", case=False, na=False))
            ]
            if not topix.empty:
                topix_row = topix.iloc[0]
                overview.topix_close = float(topix_row.get("Close", 0))
                overview.topix_change_pct = float(topix_row.get("ChangeRate", 0) or 0)
                overview.topix_change = float(topix_row.get("Change", 0) or 0)
                # Fallback: calculate change from close and change_pct if Change not available
                if overview.topix_change == 0 and overview.topix_change_pct != 0:
                    overview.topix_change = (
                        overview.topix_close * overview.topix_change_pct / 100
                    )

            # Nikkei 225 (code: 0010 or Nikkei/日経 in name)
            nikkei = indices_df[
                (indices_df["Code"] == "0010") |
                (indices_df["Code"].str.contains("0010", na=False)) |
                (indices_df.get("IndexName", pd.Series()).str.contains("Nikkei|日経", case=False, na=False, regex=True))
            ]
            if not nikkei.empty:
                nikkei_row = nikkei.iloc[0]
                overview.nikkei225_close = float(nikkei_row.get("Close", 0))
                overview.nikkei225_change_pct = float(nikkei_row.get("ChangeRate", 0) or 0)
                overview.nikkei225_change = float(nikkei_row.get("Change", 0) or 0)
                # Fallback: calculate change from close and change_pct if Change not available
                if overview.nikkei225_change == 0 and overview.nikkei225_change_pct != 0:
                    overview.nikkei225_change = (
                        overview.nikkei225_close * overview.nikkei225_change_pct / 100
                    )

        return overview

    def calculate_market_breadth(self, prices_df: pd.DataFrame) -> dict[str, float]:
        """Calculate market breadth indicators.

        Args:
            prices_df: DataFrame containing stock price data.

        Returns:
            Dictionary containing breadth indicators:
                - advance_decline_ratio: Ratio of advancing to declining issues.
                - advance_percentage: Percentage of advancing issues.
                - decline_percentage: Percentage of declining issues.
        """
        if prices_df.empty or "ChangeRate" not in prices_df.columns:
            return {
                "advance_decline_ratio": 0.0,
                "advance_percentage": 0.0,
                "decline_percentage": 0.0,
            }

        change_rates = prices_df["ChangeRate"].dropna()
        advancing = (change_rates > 0).sum()
        declining = (change_rates < 0).sum()
        total = len(change_rates)

        if declining == 0:
            ad_ratio = float(advancing) if advancing > 0 else 0.0
        else:
            ad_ratio = float(advancing / declining)

        return {
            "advance_decline_ratio": ad_ratio,
            "advance_percentage": float(advancing / total * 100) if total > 0 else 0.0,
            "decline_percentage": float(declining / total * 100) if total > 0 else 0.0,
        }
