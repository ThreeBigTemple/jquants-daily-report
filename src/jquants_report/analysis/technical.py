"""Technical analysis module.

This module provides functionality to calculate technical indicators such as
advance-decline ratio, moving average divergence, and new highs/lows.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass
class TechnicalIndicators:
    """Technical indicator analysis results.

    Attributes:
        date: Analysis date.
        advance_decline_ratio_25d: 25-day advance-decline ratio.
        new_highs: Number of stocks at new highs.
        new_lows: Number of stocks at new lows.
        new_high_low_ratio: Ratio of new highs to new lows.
        ma25_divergence_pct: Average divergence from 25-day moving average (%).
        ma75_divergence_pct: Average divergence from 75-day moving average (%).
        stocks_above_ma25_pct: Percentage of stocks above 25-day MA.
        stocks_above_ma75_pct: Percentage of stocks above 75-day MA.
    """

    date: str
    advance_decline_ratio_25d: float | None = None
    new_highs: int = 0
    new_lows: int = 0
    new_high_low_ratio: float | None = None
    ma25_divergence_pct: float | None = None
    ma75_divergence_pct: float | None = None
    stocks_above_ma25_pct: float | None = None
    stocks_above_ma75_pct: float | None = None


class TechnicalAnalyzer:
    """Analyzer for technical indicators."""

    def analyze(
        self,
        date: str,
        prices_df: pd.DataFrame,
        historical_df: pd.DataFrame | None = None,
    ) -> TechnicalIndicators:
        """Analyze technical indicators for a given date.

        Args:
            date: Analysis date in YYYY-MM-DD format.
            prices_df: DataFrame containing current stock price data.
            historical_df: Optional DataFrame with historical data for calculations.

        Returns:
            TechnicalIndicators: Analysis results.
        """
        indicators = TechnicalIndicators(date=date)

        # Calculate advance-decline ratio
        if historical_df is not None and not historical_df.empty:
            indicators.advance_decline_ratio_25d = self.calculate_advance_decline_ratio(
                historical_df, period=25
            )

        # Calculate new highs and lows
        if historical_df is not None and not historical_df.empty:
            new_highs, new_lows = self.calculate_new_highs_lows(prices_df, historical_df)
            indicators.new_highs = new_highs
            indicators.new_lows = new_lows

            if new_lows > 0:
                indicators.new_high_low_ratio = float(new_highs / new_lows)
            elif new_highs > 0:
                indicators.new_high_low_ratio = float(new_highs)

        # Calculate moving average divergence
        if historical_df is not None and not historical_df.empty:
            ma25_div, stocks_above_ma25 = self.calculate_ma_divergence(
                prices_df, historical_df, period=25
            )
            ma75_div, stocks_above_ma75 = self.calculate_ma_divergence(
                prices_df, historical_df, period=75
            )

            indicators.ma25_divergence_pct = ma25_div
            indicators.ma75_divergence_pct = ma75_div
            indicators.stocks_above_ma25_pct = stocks_above_ma25
            indicators.stocks_above_ma75_pct = stocks_above_ma75

        return indicators

    def calculate_advance_decline_ratio(
        self, historical_df: pd.DataFrame, period: int = 25
    ) -> float | None:
        """Calculate advance-decline ratio over a specified period.

        Args:
            historical_df: DataFrame with historical price data.
            period: Number of days to calculate ratio over.

        Returns:
            Advance-decline ratio as a percentage, or None if insufficient data.
        """
        if historical_df.empty or "ChangeRate" not in historical_df.columns:
            return None

        # Get most recent period days
        recent_data = historical_df.tail(period * 1000)  # Approximate by large multiple

        if len(recent_data) < period:
            return None

        # Group by date and count advancing/declining issues
        daily_stats = recent_data.groupby("Date").agg(
            advancing=("ChangeRate", lambda x: (x > 0).sum()),
            declining=("ChangeRate", lambda x: (x < 0).sum()),
        )

        # Take last N days
        daily_stats = daily_stats.tail(period)

        # Require at least 80% of the period (e.g., 20 days for 25-day period)
        min_required = int(period * 0.8)
        if len(daily_stats) < min_required:
            return None

        total_advancing = daily_stats["advancing"].sum()
        total_declining = daily_stats["declining"].sum()

        if total_declining == 0:
            return None

        # Return as percentage
        ratio = (total_advancing / total_declining) * 100
        return float(ratio)

    def calculate_new_highs_lows(
        self, current_df: pd.DataFrame, historical_df: pd.DataFrame, period: int = 52
    ) -> tuple[int, int]:
        """Calculate number of stocks at new highs and lows.

        Args:
            current_df: DataFrame with current price data.
            historical_df: DataFrame with historical data.
            period: Number of weeks for new high/low (default: 52 weeks = 252 days).

        Returns:
            Tuple of (new_highs_count, new_lows_count).
        """
        if current_df.empty or historical_df.empty:
            return 0, 0

        # Calculate period highs and lows for each stock
        trading_days = period * 5  # Approximate trading days
        period_highs = (
            historical_df.groupby("Code")["High"]
            .tail(trading_days)
            .groupby(
                historical_df[
                    historical_df.index.isin(historical_df.groupby("Code").tail(trading_days).index)
                ]["Code"]
            )
            .max()
        )

        period_lows = (
            historical_df.groupby("Code")["Low"]
            .tail(trading_days)
            .groupby(
                historical_df[
                    historical_df.index.isin(historical_df.groupby("Code").tail(trading_days).index)
                ]["Code"]
            )
            .min()
        )

        # Merge with current data
        result_df = current_df.copy()

        if "High" not in result_df.columns or "Low" not in result_df.columns:
            return 0, 0

        result_df = result_df.merge(
            period_highs.rename("PeriodHigh"),
            left_on="Code",
            right_index=True,
            how="left",
        )
        result_df = result_df.merge(
            period_lows.rename("PeriodLow"),
            left_on="Code",
            right_index=True,
            how="left",
        )

        # Count new highs and lows
        new_highs = int((result_df["High"] >= result_df["PeriodHigh"]).sum())
        new_lows = int((result_df["Low"] <= result_df["PeriodLow"]).sum())

        return new_highs, new_lows

    def calculate_ma_divergence(
        self, current_df: pd.DataFrame, historical_df: pd.DataFrame, period: int = 25
    ) -> tuple[float | None, float | None]:
        """Calculate moving average divergence.

        Args:
            current_df: DataFrame with current price data.
            historical_df: DataFrame with historical data.
            period: Moving average period (days).

        Returns:
            Tuple of (average_divergence_pct, stocks_above_ma_pct).
        """
        if current_df.empty or historical_df.empty or "Close" not in historical_df.columns:
            return None, None

        # Calculate moving average for each stock
        ma_values = (
            historical_df.groupby("Code")["Close"]
            .tail(period)
            .groupby(
                historical_df[
                    historical_df.index.isin(historical_df.groupby("Code").tail(period).index)
                ]["Code"]
            )
            .mean()
        )

        # Merge with current data
        result_df = current_df.copy()

        if "Close" not in result_df.columns:
            return None, None

        result_df = result_df.merge(
            ma_values.rename(f"MA{period}"),
            left_on="Code",
            right_index=True,
            how="left",
        )

        # Calculate divergence percentage
        result_df[f"MA{period}Divergence"] = (
            (result_df["Close"] - result_df[f"MA{period}"]) / result_df[f"MA{period}"] * 100
        )

        # Filter out invalid values
        valid_divergence = result_df[f"MA{period}Divergence"].dropna()

        if len(valid_divergence) == 0:
            return None, None

        avg_divergence = float(valid_divergence.mean())

        # Calculate percentage of stocks above MA
        stocks_above_ma = int((result_df["Close"] > result_df[f"MA{period}"]).sum())
        total_stocks = int((~result_df[f"MA{period}"].isna()).sum())

        stocks_above_ma_pct = (
            float(stocks_above_ma / total_stocks * 100) if total_stocks > 0 else None
        )

        return avg_divergence, stocks_above_ma_pct

    def calculate_rsi(
        self, historical_df: pd.DataFrame, code: str, period: int = 14
    ) -> float | None:
        """Calculate Relative Strength Index for a specific stock.

        Args:
            historical_df: DataFrame with historical price data.
            code: Stock code.
            period: RSI period (default: 14 days).

        Returns:
            RSI value (0-100), or None if insufficient data.
        """
        stock_data = historical_df[historical_df["Code"] == code].copy()

        if len(stock_data) < period + 1 or "Close" not in stock_data.columns:
            return None

        # Calculate price changes
        stock_data = stock_data.sort_values("Date")
        stock_data["PriceChange"] = stock_data["Close"].diff()

        # Separate gains and losses
        gains = stock_data["PriceChange"].clip(lower=0)
        losses = -stock_data["PriceChange"].clip(upper=0)

        # Calculate average gains and losses
        avg_gain = gains.tail(period).mean()
        avg_loss = losses.tail(period).mean()

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)
