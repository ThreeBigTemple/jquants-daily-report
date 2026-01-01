"""Individual stock analysis module.

This module provides functionality to identify notable stocks including
top gainers/losers, high volume stocks, and limit hits.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class StockInfo:
    """Individual stock information.

    Attributes:
        code: Stock code.
        name: Stock name.
        close: Closing price.
        change: Price change from previous day.
        change_pct: Percentage change from previous day.
        volume: Trading volume.
        turnover_value: Trading value.
        sector_name: Sector name (optional).
        high_limit: Whether stock hit upper price limit (optional).
        low_limit: Whether stock hit lower price limit (optional).
        year_high: Whether stock reached 52-week high (optional).
        year_low: Whether stock reached 52-week low (optional).
        volume_ratio: Volume ratio compared to average (optional).
    """

    code: str
    name: str
    close: float
    change: float
    change_pct: float
    volume: float
    turnover_value: float = 0.0
    sector_name: str = ""
    high_limit: bool | None = None
    low_limit: bool | None = None
    year_high: bool | None = None
    year_low: bool | None = None
    volume_ratio: float | None = None


class StockAnalyzer:
    """Analyzer for individual stock performance."""

    def get_top_gainers(self, prices_df: pd.DataFrame, top_n: int = 10) -> list[StockInfo]:
        """Get top N gaining stocks by percentage change.

        Args:
            prices_df: DataFrame containing stock price data.
            top_n: Number of top gainers to return.

        Returns:
            List of top gaining stocks.
        """
        if prices_df.empty or "ChangeRate" not in prices_df.columns:
            return []

        # Filter out invalid data and sort by change rate
        valid_df = prices_df[prices_df["ChangeRate"].notna()].copy()
        sorted_df = valid_df.nlargest(top_n, "ChangeRate")

        return self._convert_to_stock_info(sorted_df)

    def get_top_losers(self, prices_df: pd.DataFrame, top_n: int = 10) -> list[StockInfo]:
        """Get top N losing stocks by percentage change.

        Args:
            prices_df: DataFrame containing stock price data.
            top_n: Number of top losers to return.

        Returns:
            List of top losing stocks (only negative change rates).
        """
        if prices_df.empty or "ChangeRate" not in prices_df.columns:
            return []

        # Filter out invalid data and only include negative change rates
        valid_df = prices_df[prices_df["ChangeRate"].notna()].copy()
        losers_df = valid_df[valid_df["ChangeRate"] < 0]
        sorted_df = losers_df.nsmallest(top_n, "ChangeRate")

        return self._convert_to_stock_info(sorted_df)

    def get_high_volume_stocks(
        self,
        prices_df: pd.DataFrame,
        historical_df: pd.DataFrame | None = None,
        volume_threshold: float = 2.0,
        top_n: int = 10,
    ) -> list[StockInfo]:
        """Get stocks with high volume compared to their average.

        Args:
            prices_df: DataFrame containing current stock price data.
            historical_df: Optional DataFrame with historical data to calculate average volume.
            volume_threshold: Minimum ratio of current volume to average (default: 2.0x).
            top_n: Number of stocks to return.

        Returns:
            List of high volume stocks.
        """
        if prices_df.empty or "Volume" not in prices_df.columns:
            return []

        result_df = prices_df.copy()

        # Calculate volume ratio if historical data is available
        if historical_df is not None and not historical_df.empty:
            # Calculate 20-day average volume for each stock
            avg_volumes = (
                historical_df.groupby("Code")["Volume"]
                .tail(20)
                .groupby(historical_df.groupby("Code").cumcount() // 20)
                .mean()
            )

            # Merge with current data
            result_df = result_df.merge(
                avg_volumes.rename("AvgVolume"),
                left_on="Code",
                right_index=True,
                how="left",
            )

            result_df["VolumeRatio"] = result_df["Volume"] / result_df["AvgVolume"]
            result_df = result_df[result_df["VolumeRatio"] >= volume_threshold]
            result_df = result_df.nlargest(top_n, "VolumeRatio")
        else:
            # Just return top volume stocks
            result_df = result_df.nlargest(top_n, "Volume")

        stocks = self._convert_to_stock_info(result_df)

        # Add volume ratio if available
        if "VolumeRatio" in result_df.columns:
            for i, stock in enumerate(stocks):
                stock.volume_ratio = float(result_df.iloc[i]["VolumeRatio"])

        return stocks

    def get_limit_hits(self, prices_df: pd.DataFrame) -> dict[str, list[StockInfo]]:
        """Get stocks that hit price limits.

        Args:
            prices_df: DataFrame containing stock price data with High/Low limit flags.

        Returns:
            Dictionary with 'upper_limit' and 'lower_limit' lists of stocks.
        """
        result: dict[str, list[StockInfo]] = {
            "upper_limit": [],
            "lower_limit": [],
        }

        if prices_df.empty:
            return result

        # Check for upper limit hits
        if "HighLimit" in prices_df.columns:
            upper_df = prices_df[prices_df["HighLimit"] == True].copy()  # noqa: E712
            upper_stocks = self._convert_to_stock_info(upper_df)
            for stock in upper_stocks:
                stock.high_limit = True
            result["upper_limit"] = upper_stocks

        # Check for lower limit hits
        if "LowLimit" in prices_df.columns:
            lower_df = prices_df[prices_df["LowLimit"] == True].copy()  # noqa: E712
            lower_stocks = self._convert_to_stock_info(lower_df)
            for stock in lower_stocks:
                stock.low_limit = True
            result["lower_limit"] = lower_stocks

        return result

    def get_52week_highs_lows(
        self, prices_df: pd.DataFrame, historical_df: pd.DataFrame | None = None
    ) -> dict[str, list[StockInfo]]:
        """Get stocks that reached 52-week highs or lows.

        Args:
            prices_df: DataFrame containing current stock price data.
            historical_df: Optional DataFrame with historical data (252 trading days).

        Returns:
            Dictionary with 'year_high' and 'year_low' lists of stocks.
        """
        result: dict[str, list[StockInfo]] = {
            "year_high": [],
            "year_low": [],
        }

        if prices_df.empty or historical_df is None or historical_df.empty:
            return result

        # Calculate 52-week high/low for each stock
        year_highs = historical_df.groupby("Code")["High"].max()
        year_lows = historical_df.groupby("Code")["Low"].min()

        # Merge with current data
        result_df = prices_df.copy()
        result_df = result_df.merge(
            year_highs.rename("YearHigh"), left_on="Code", right_index=True, how="left"
        )
        result_df = result_df.merge(
            year_lows.rename("YearLow"), left_on="Code", right_index=True, how="left"
        )

        # Find stocks at year high
        if "High" in result_df.columns:
            year_high_df = result_df[result_df["High"] >= result_df["YearHigh"]].copy()
            year_high_stocks = self._convert_to_stock_info(year_high_df)
            for stock in year_high_stocks:
                stock.year_high = True
            result["year_high"] = year_high_stocks

        # Find stocks at year low
        if "Low" in result_df.columns:
            year_low_df = result_df[result_df["Low"] <= result_df["YearLow"]].copy()
            year_low_stocks = self._convert_to_stock_info(year_low_df)
            for stock in year_low_stocks:
                stock.year_low = True
            result["year_low"] = year_low_stocks

        return result

    def get_top_turnover_stocks(
        self, prices_df: pd.DataFrame, top_n: int = 10
    ) -> list[StockInfo]:
        """Get top N stocks by trading turnover value.

        Args:
            prices_df: DataFrame containing stock price data.
            top_n: Number of top stocks to return.

        Returns:
            List of top turnover stocks.
        """
        if prices_df.empty or "TurnoverValue" not in prices_df.columns:
            return []

        # Filter out invalid data and sort by turnover value
        valid_df = prices_df[prices_df["TurnoverValue"].notna()].copy()
        sorted_df = valid_df.nlargest(top_n, "TurnoverValue")

        return self._convert_to_stock_info(sorted_df)

    def _convert_to_stock_info(self, df: pd.DataFrame) -> list[StockInfo]:
        """Convert DataFrame to list of StockInfo objects.

        Args:
            df: DataFrame containing stock data.

        Returns:
            List of StockInfo objects.
        """
        stocks: list[StockInfo] = []

        for _, row in df.iterrows():
            code = str(row.get("Code", ""))
            name = str(row.get("CompanyName", row.get("Name", "")))
            close = float(row.get("Close", 0.0))
            change_pct = float(row.get("ChangeRate", 0.0))
            volume = float(row.get("Volume", 0.0))
            turnover_value = float(row.get("TurnoverValue", 0.0))

            # Calculate price change from previous close or from change_pct
            prev_close = row.get("PrevClose")
            if prev_close is not None and not pd.isna(prev_close):
                change = close - float(prev_close)
            elif change_pct != 0:
                # Calculate change from change_pct: change = close - (close / (1 + pct/100))
                change = close - (close / (1 + change_pct / 100))
            else:
                change = 0.0

            sector_name = ""
            if "Sector33CodeName" in row:
                sector_name = str(row["Sector33CodeName"])

            stocks.append(
                StockInfo(
                    code=code,
                    name=name,
                    close=close,
                    change=change,
                    change_pct=change_pct,
                    volume=volume,
                    turnover_value=turnover_value,
                    sector_name=sector_name,
                )
            )

        return stocks
