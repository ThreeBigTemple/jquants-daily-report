"""Supply and demand analysis module.

This module provides functionality to analyze market supply and demand through
investor trading patterns and margin trading data.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class InvestorTradingSummary:
    """Investor trading summary by investor type.

    Attributes:
        investor_type: Type of investor (e.g., '個人', '外国人', '法人等').
        buy_value: Total buy value (million yen).
        sell_value: Total sell value (million yen).
        net_value: Net value (buy - sell, million yen).
        buy_volume: Total buy volume (shares).
        sell_volume: Total sell volume (shares).
        net_volume: Net volume (buy - sell, shares).
    """

    investor_type: str
    buy_value: float = 0.0
    sell_value: float = 0.0
    net_value: float = 0.0
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    net_volume: float = 0.0


@dataclass
class MarginTradingSummary:
    """Margin trading summary.

    Attributes:
        date: Analysis date.
        margin_buy_balance: Outstanding margin buy balance (shares).
        margin_sell_balance: Outstanding margin sell balance (shares).
        margin_ratio: Margin ratio (buy/sell).
        margin_buy_value: Margin buy value (million yen).
        margin_sell_value: Margin sell value (million yen).
        net_margin_value: Net margin value (million yen).
    """

    date: str
    margin_buy_balance: float = 0.0
    margin_sell_balance: float = 0.0
    margin_ratio: float | None = None
    margin_buy_value: float = 0.0
    margin_sell_value: float = 0.0
    net_margin_value: float = 0.0


@dataclass
class SupplyDemandAnalysis:
    """Combined supply and demand analysis.

    Attributes:
        date: Analysis date.
        investor_trading: List of investor trading summaries by type.
        margin_trading: Margin trading summary.
        foreign_net_value: Foreign investor net trading value (million yen).
        individual_net_value: Individual investor net trading value (million yen).
    """

    date: str
    investor_trading: list[InvestorTradingSummary]
    margin_trading: MarginTradingSummary | None = None
    foreign_net_value: float = 0.0
    individual_net_value: float = 0.0


class SupplyDemandAnalyzer:
    """Analyzer for supply and demand indicators."""

    # Investor type name mappings
    INVESTOR_TYPE_NAMES: dict[str, str] = {
        "1": "個人",
        "2": "外国人",
        "3": "証券会社",
        "4": "投資信託",
        "5": "事業法人",
        "6": "その他法人",
        "7": "金融機関",
        "8": "信託銀行",
        "9": "その他",
    }

    def analyze_investor_trading(self, trading_df: pd.DataFrame) -> list[InvestorTradingSummary]:
        """Analyze investor trading by investor type.

        Args:
            trading_df: DataFrame containing investor trading data with columns:
                - InvestorType: Investor type code
                - BuyValue: Buy value
                - SellValue: Sell value
                - BuyVolume: Buy volume
                - SellVolume: Sell volume

        Returns:
            List of InvestorTradingSummary objects.
        """
        if trading_df.empty:
            return []

        summaries: list[InvestorTradingSummary] = []

        # Group by investor type
        if "InvestorType" in trading_df.columns:
            grouped = trading_df.groupby("InvestorType")

            for investor_type_code, group in grouped:
                investor_type = self.INVESTOR_TYPE_NAMES.get(
                    str(investor_type_code), str(investor_type_code)
                )

                buy_value = float(group["BuyValue"].sum()) if "BuyValue" in group.columns else 0.0
                sell_value = (
                    float(group["SellValue"].sum()) if "SellValue" in group.columns else 0.0
                )
                buy_volume = (
                    float(group["BuyVolume"].sum()) if "BuyVolume" in group.columns else 0.0
                )
                sell_volume = (
                    float(group["SellVolume"].sum()) if "SellVolume" in group.columns else 0.0
                )

                summaries.append(
                    InvestorTradingSummary(
                        investor_type=investor_type,
                        buy_value=buy_value,
                        sell_value=sell_value,
                        net_value=buy_value - sell_value,
                        buy_volume=buy_volume,
                        sell_volume=sell_volume,
                        net_volume=buy_volume - sell_volume,
                    )
                )

        # Sort by absolute net value (descending)
        summaries.sort(key=lambda x: abs(x.net_value), reverse=True)

        return summaries

    def analyze_margin_trading(
        self, date: str, margin_df: pd.DataFrame
    ) -> MarginTradingSummary | None:
        """Analyze margin trading data.

        Args:
            date: Analysis date.
            margin_df: DataFrame containing margin trading data with columns:
                - MarginBuyBalance: Outstanding margin buy balance
                - MarginSellBalance: Outstanding margin sell balance
                - MarginBuyValue: Margin buy value
                - MarginSellValue: Margin sell value

        Returns:
            MarginTradingSummary object or None if no data.
        """
        if margin_df.empty:
            return None

        summary = MarginTradingSummary(date=date)

        # Aggregate margin data
        if "MarginBuyBalance" in margin_df.columns:
            summary.margin_buy_balance = float(margin_df["MarginBuyBalance"].sum())

        if "MarginSellBalance" in margin_df.columns:
            summary.margin_sell_balance = float(margin_df["MarginSellBalance"].sum())

        # Calculate margin ratio (lending/borrowing)
        if summary.margin_sell_balance > 0:
            summary.margin_ratio = summary.margin_buy_balance / summary.margin_sell_balance

        if "MarginBuyValue" in margin_df.columns:
            summary.margin_buy_value = float(margin_df["MarginBuyValue"].sum())

        if "MarginSellValue" in margin_df.columns:
            summary.margin_sell_value = float(margin_df["MarginSellValue"].sum())

        summary.net_margin_value = summary.margin_buy_value - summary.margin_sell_value

        return summary

    def analyze(
        self,
        date: str,
        trading_df: pd.DataFrame | None = None,
        margin_df: pd.DataFrame | None = None,
    ) -> SupplyDemandAnalysis:
        """Perform comprehensive supply and demand analysis.

        Args:
            date: Analysis date.
            trading_df: Optional DataFrame with investor trading data.
            margin_df: Optional DataFrame with margin trading data.

        Returns:
            SupplyDemandAnalysis object with complete analysis.
        """
        investor_summaries: list[InvestorTradingSummary] = []
        margin_summary: MarginTradingSummary | None = None
        foreign_net = 0.0
        individual_net = 0.0

        # Analyze investor trading
        if trading_df is not None and not trading_df.empty:
            investor_summaries = self.analyze_investor_trading(trading_df)

            # Extract specific investor types
            for summary in investor_summaries:
                if summary.investor_type == "外国人":
                    foreign_net = summary.net_value
                elif summary.investor_type == "個人":
                    individual_net = summary.net_value

        # Analyze margin trading
        if margin_df is not None and not margin_df.empty:
            margin_summary = self.analyze_margin_trading(date, margin_df)

        return SupplyDemandAnalysis(
            date=date,
            investor_trading=investor_summaries,
            margin_trading=margin_summary,
            foreign_net_value=foreign_net,
            individual_net_value=individual_net,
        )

    def get_top_net_buyers(
        self, investor_summaries: list[InvestorTradingSummary], top_n: int = 3
    ) -> list[InvestorTradingSummary]:
        """Get top N net buying investor types.

        Args:
            investor_summaries: List of InvestorTradingSummary objects.
            top_n: Number of top buyers to return.

        Returns:
            List of top net buying investor types.
        """
        sorted_summaries = sorted(investor_summaries, key=lambda x: x.net_value, reverse=True)
        return sorted_summaries[:top_n]

    def get_top_net_sellers(
        self, investor_summaries: list[InvestorTradingSummary], top_n: int = 3
    ) -> list[InvestorTradingSummary]:
        """Get top N net selling investor types.

        Args:
            investor_summaries: List of InvestorTradingSummary objects.
            top_n: Number of top sellers to return.

        Returns:
            List of top net selling investor types.
        """
        sorted_summaries = sorted(investor_summaries, key=lambda x: x.net_value)
        return sorted_summaries[:top_n]
