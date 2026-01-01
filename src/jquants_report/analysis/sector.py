"""Sector analysis module.

This module provides functionality to analyze sector performance across
Japan's 33 industry sectors.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class SectorPerformance:
    """Sector performance data.

    Attributes:
        sector_code: Sector code (33 industry classification).
        sector_name: Sector name in Japanese.
        average_change_pct: Average percentage change of stocks in the sector.
        issue_count: Number of issues in the sector.
        advancing_count: Number of advancing issues.
        declining_count: Number of declining issues.
        total_volume: Total trading volume in the sector.
        total_value: Total trading value in the sector.
    """

    sector_code: str
    sector_name: str
    average_change_pct: float
    issue_count: int = 0
    advancing_count: int = 0
    declining_count: int = 0
    total_volume: float = 0.0
    total_value: float = 0.0


# 33業種分類マッピング
SECTOR_NAMES: dict[str, str] = {
    "0050": "水産・農林業",
    "1050": "鉱業",
    "2050": "建設業",
    "3050": "食料品",
    "3100": "繊維製品",
    "3150": "パルプ・紙",
    "3200": "化学",
    "3250": "医薬品",
    "3300": "石油・石炭製品",
    "3350": "ゴム製品",
    "3400": "ガラス・土石製品",
    "3450": "鉄鋼",
    "3500": "非鉄金属",
    "3550": "金属製品",
    "3600": "機械",
    "3650": "電気機器",
    "3700": "輸送用機器",
    "3750": "精密機器",
    "3800": "その他製品",
    "4050": "電気・ガス業",
    "5050": "陸運業",
    "5100": "海運業",
    "5150": "空運業",
    "5200": "倉庫・運輸関連業",
    "6050": "情報・通信業",
    "6100": "卸売業",
    "6150": "小売業",
    "7050": "銀行業",
    "7100": "証券、商品先物取引業",
    "7150": "保険業",
    "7200": "その他金融業",
    "8050": "不動産業",
    "9050": "サービス業",
}


class SectorAnalyzer:
    """Analyzer for sector performance."""

    def __init__(self) -> None:
        """Initialize SectorAnalyzer."""
        self.sector_names = SECTOR_NAMES

    def analyze_sectors(self, prices_df: pd.DataFrame) -> list[SectorPerformance]:
        """Analyze performance by sector.

        Args:
            prices_df: DataFrame containing stock price data with columns:
                - Code: Stock code
                - Sector33Code: 33-industry sector code
                - Sector33CodeName: Sector name
                - Close: Closing price
                - ChangeRate: Change rate (percentage)
                - Volume: Trading volume
                - TurnoverValue: Trading value

        Returns:
            List of SectorPerformance objects sorted by average change percentage.
        """
        if prices_df.empty or "Sector33Code" not in prices_df.columns:
            return []

        sector_results: list[SectorPerformance] = []

        # Group by sector
        grouped = prices_df.groupby("Sector33Code")

        for sector_code, group in grouped:
            if pd.isna(sector_code) or sector_code == "":
                continue

            sector_code_str = str(sector_code)

            # Get sector name
            sector_name = self.sector_names.get(sector_code_str, sector_code_str)
            if "Sector33CodeName" in group.columns:
                sector_name_from_data = group["Sector33CodeName"].iloc[0]
                if pd.notna(sector_name_from_data) and sector_name_from_data != "":
                    sector_name = str(sector_name_from_data)

            # Calculate statistics
            change_rates = (
                group["ChangeRate"].dropna()
                if "ChangeRate" in group.columns
                else pd.Series(dtype=float)
            )

            average_change = float(change_rates.mean()) if len(change_rates) > 0 else 0.0
            issue_count = len(group)
            advancing = int((change_rates > 0).sum()) if len(change_rates) > 0 else 0
            declining = int((change_rates < 0).sum()) if len(change_rates) > 0 else 0

            total_volume = float(group["Volume"].sum()) if "Volume" in group.columns else 0.0
            total_value = (
                float(group["TurnoverValue"].sum()) if "TurnoverValue" in group.columns else 0.0
            )

            sector_results.append(
                SectorPerformance(
                    sector_code=sector_code_str,
                    sector_name=sector_name,
                    average_change_pct=average_change,
                    issue_count=issue_count,
                    advancing_count=advancing,
                    declining_count=declining,
                    total_volume=total_volume,
                    total_value=total_value,
                )
            )

        # Sort by average change percentage (descending)
        sector_results.sort(key=lambda x: x.average_change_pct, reverse=True)

        return sector_results

    def get_top_sectors(
        self, sector_performances: list[SectorPerformance], top_n: int = 10
    ) -> list[SectorPerformance]:
        """Get top N performing sectors.

        Args:
            sector_performances: List of SectorPerformance objects.
            top_n: Number of top sectors to return.

        Returns:
            List of top N performing sectors.
        """
        return sector_performances[:top_n]

    def get_bottom_sectors(
        self, sector_performances: list[SectorPerformance], bottom_n: int = 10
    ) -> list[SectorPerformance]:
        """Get bottom N performing sectors.

        Args:
            sector_performances: List of SectorPerformance objects.
            bottom_n: Number of bottom sectors to return.

        Returns:
            List of bottom N performing sectors.
        """
        return sector_performances[-bottom_n:][::-1]  # Reverse to show worst first
