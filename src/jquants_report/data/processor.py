"""Data processing and normalization for J-Quants data.

This module provides data cleaning, normalization, and transformation
utilities for various J-Quants API data types.
"""

import logging
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


class DataProcessor:
    """Processes and normalizes J-Quants API data.

    Provides data cleaning, type conversion, and normalization
    for various market data types.
    """

    # Standard column name mappings for consistency
    COLUMN_MAPPINGS = {
        "Code": "code",
        "Date": "date",
        "Open": "open",
        "High": "high",
        "Low": "low",
        "Close": "close",
        "Volume": "volume",
        "TurnoverValue": "turnover_value",
        "AdjustmentFactor": "adjustment_factor",
        "AdjustmentOpen": "adjusted_open",
        "AdjustmentHigh": "adjusted_high",
        "AdjustmentLow": "adjusted_low",
        "AdjustmentClose": "adjusted_close",
        "AdjustmentVolume": "adjusted_volume",
    }

    def __init__(self):
        """Initialize DataProcessor."""
        pass

    def _standardize_columns(
        self, df: pd.DataFrame, column_mapping: dict[str, str] | None = None
    ) -> pd.DataFrame:
        """Standardize column names.

        Args:
            df: Input DataFrame.
            column_mapping: Optional custom column mapping.

        Returns:
            DataFrame with standardized column names.
        """
        if df.empty:
            return df

        mapping = column_mapping or self.COLUMN_MAPPINGS
        df = df.rename(columns=mapping)
        logger.debug(f"Standardized columns: {list(df.columns)}")
        return df

    def _convert_date_columns(self, df: pd.DataFrame, date_columns: list[str]) -> pd.DataFrame:
        """Convert string columns to datetime.

        Args:
            df: Input DataFrame.
            date_columns: List of column names to convert.

        Returns:
            DataFrame with converted date columns.
        """
        if df.empty:
            return df

        for col in date_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_datetime(df[col])
                    logger.debug(f"Converted {col} to datetime")
                except Exception as e:
                    logger.warning(f"Failed to convert {col} to datetime: {e}")

        return df

    def _convert_numeric_columns(
        self, df: pd.DataFrame, numeric_columns: list[str]
    ) -> pd.DataFrame:
        """Convert columns to numeric types.

        Args:
            df: Input DataFrame.
            numeric_columns: List of column names to convert.

        Returns:
            DataFrame with converted numeric columns.
        """
        if df.empty:
            return df

        for col in numeric_columns:
            if col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col], errors="coerce")
                    logger.debug(f"Converted {col} to numeric")
                except Exception as e:
                    logger.warning(f"Failed to convert {col} to numeric: {e}")

        return df

    def _remove_invalid_rows(self, df: pd.DataFrame, required_columns: list[str]) -> pd.DataFrame:
        """Remove rows with missing required values.

        Args:
            df: Input DataFrame.
            required_columns: List of columns that must have values.

        Returns:
            DataFrame with invalid rows removed.
        """
        if df.empty:
            return df

        initial_count = len(df)
        df = df.dropna(subset=required_columns)
        removed_count = initial_count - len(df)

        if removed_count > 0:
            logger.info(f"Removed {removed_count} rows with missing required values")

        return df

    def process_daily_quotes(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process daily stock quotes data.

        Args:
            df: Raw daily quotes DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_daily_quotes")
            return df

        logger.info(f"Processing {len(df)} daily quote records")

        # Standardize column names
        df = self._standardize_columns(df)

        # Convert date columns
        df = self._convert_date_columns(df, ["date"])

        # Convert numeric columns
        numeric_cols = [
            "open",
            "high",
            "low",
            "close",
            "volume",
            "turnover_value",
            "adjustment_factor",
            "adjusted_open",
            "adjusted_high",
            "adjusted_low",
            "adjusted_close",
            "adjusted_volume",
        ]
        df = self._convert_numeric_columns(df, numeric_cols)

        # Remove rows without essential data
        required_cols = ["code", "date", "close"]
        df = self._remove_invalid_rows(df, required_cols)

        # Add derived columns
        if "close" in df.columns and "open" in df.columns:
            df["price_change"] = df["close"] - df["open"]
            df["price_change_pct"] = (df["price_change"] / df["open"]) * 100

        # Sort by code and date
        if "code" in df.columns and "date" in df.columns:
            df = df.sort_values(["code", "date"]).reset_index(drop=True)

        logger.info(f"Processed daily quotes: {len(df)} records")
        return df

    def process_listed_info(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process listed company information.

        Args:
            df: Raw listed info DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_listed_info")
            return df

        logger.info(f"Processing {len(df)} listed info records")

        # Standardize common column names
        column_mapping = {
            "Code": "code",
            "CompanyName": "company_name",
            "CompanyNameEnglish": "company_name_en",
            "Sector17Code": "sector_17_code",
            "Sector17CodeName": "sector_17_name",
            "Sector33Code": "sector_33_code",
            "Sector33CodeName": "sector_33_name",
            "ScaleCategory": "scale_category",
            "MarketCode": "market_code",
            "MarketCodeName": "market_name",
        }
        df = self._standardize_columns(df, column_mapping)

        # Remove duplicates based on code
        if "code" in df.columns:
            initial_count = len(df)
            df = df.drop_duplicates(subset=["code"], keep="last")
            if len(df) < initial_count:
                logger.info(f"Removed {initial_count - len(df)} duplicate codes")

        logger.info(f"Processed listed info: {len(df)} records")
        return df

    def process_indices(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process index data.

        Args:
            df: Raw indices DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_indices")
            return df

        logger.info(f"Processing {len(df)} index records")

        # Standardize column names
        column_mapping = {
            "Date": "date",
            "Code": "code",
            "IndexName": "index_name",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
        }
        df = self._standardize_columns(df, column_mapping)

        # Convert date columns
        df = self._convert_date_columns(df, ["date"])

        # Convert numeric columns
        numeric_cols = ["open", "high", "low", "close"]
        df = self._convert_numeric_columns(df, numeric_cols)

        # Add derived columns
        if "close" in df.columns and "open" in df.columns:
            df["change"] = df["close"] - df["open"]
            df["change_pct"] = (df["change"] / df["open"]) * 100

        # Sort by date and code
        if "date" in df.columns and "code" in df.columns:
            df = df.sort_values(["date", "code"]).reset_index(drop=True)

        logger.info(f"Processed indices: {len(df)} records")
        return df

    def process_trades_spec(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process investor type trading data.

        Args:
            df: Raw trades spec DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_trades_spec")
            return df

        logger.info(f"Processing {len(df)} trades spec records")

        # Convert date columns
        df = self._convert_date_columns(df, ["Date", "PublishedDate"])

        # Convert numeric columns - these vary by API response
        # Find all numeric-like columns
        for col in df.columns:
            if df[col].dtype == "object":
                # Try to convert to numeric
                try:
                    df[col] = pd.to_numeric(df[col], errors="ignore")
                except Exception:
                    pass

        logger.info(f"Processed trades spec: {len(df)} records")
        return df

    def process_margin_interest(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process margin trading balance data.

        Args:
            df: Raw margin interest DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_margin_interest")
            return df

        logger.info(f"Processing {len(df)} margin interest records")

        # Standardize column names
        column_mapping = {
            "Code": "code",
            "Date": "date",
            "MarginBuy": "margin_buy",
            "MarginSell": "margin_sell",
            "MarginBuyBalance": "margin_buy_balance",
            "MarginSellBalance": "margin_sell_balance",
        }
        df = self._standardize_columns(df, column_mapping)

        # Convert date columns
        df = self._convert_date_columns(df, ["date"])

        # Convert numeric columns
        numeric_cols = ["margin_buy", "margin_sell", "margin_buy_balance", "margin_sell_balance"]
        df = self._convert_numeric_columns(df, numeric_cols)

        # Sort by code and date
        if "code" in df.columns and "date" in df.columns:
            df = df.sort_values(["code", "date"]).reset_index(drop=True)

        logger.info(f"Processed margin interest: {len(df)} records")
        return df

    def process_short_selling(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process short selling ratio data.

        Args:
            df: Raw short selling DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_short_selling")
            return df

        logger.info(f"Processing {len(df)} short selling records")

        # Standardize column names
        column_mapping = {
            "Code": "code",
            "Date": "date",
            "ShortSellingRatio": "short_selling_ratio",
            "ShortSellingVolume": "short_selling_volume",
            "TotalVolume": "total_volume",
        }
        df = self._standardize_columns(df, column_mapping)

        # Convert date columns
        df = self._convert_date_columns(df, ["date"])

        # Convert numeric columns
        numeric_cols = ["short_selling_ratio", "short_selling_volume", "total_volume"]
        df = self._convert_numeric_columns(df, numeric_cols)

        # Calculate ratio if not present
        if (
            "short_selling_ratio" not in df.columns
            and "short_selling_volume" in df.columns
            and "total_volume" in df.columns
        ):
            df["short_selling_ratio"] = df["short_selling_volume"] / df["total_volume"] * 100

        # Sort by code and date
        if "code" in df.columns and "date" in df.columns:
            df = df.sort_values(["code", "date"]).reset_index(drop=True)

        logger.info(f"Processed short selling: {len(df)} records")
        return df

    def process_statements(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process financial statements data.

        Args:
            df: Raw statements DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_statements")
            return df

        logger.info(f"Processing {len(df)} statement records")

        # Convert date columns
        date_cols = ["DisclosedDate", "CurrentPeriodEndDate", "CurrentFiscalYearEndDate"]
        df = self._convert_date_columns(df, date_cols)

        # Convert numeric columns automatically
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = pd.to_numeric(df[col], errors="ignore")
                except Exception:
                    pass

        logger.info(f"Processed statements: {len(df)} records")
        return df

    def process_announcement(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process earnings announcement schedule.

        Args:
            df: Raw announcement DataFrame.

        Returns:
            Processed and normalized DataFrame.
        """
        if df.empty:
            logger.warning("Empty DataFrame provided to process_announcement")
            return df

        logger.info(f"Processing {len(df)} announcement records")

        # Standardize column names
        column_mapping = {
            "Code": "code",
            "Date": "date",
            "CompanyName": "company_name",
        }
        df = self._standardize_columns(df, column_mapping)

        # Convert date columns
        df = self._convert_date_columns(df, ["date", "Date"])

        # Sort by date
        if "date" in df.columns:
            df = df.sort_values("date").reset_index(drop=True)

        logger.info(f"Processed announcement: {len(df)} records")
        return df

    def calculate_statistics(
        self, df: pd.DataFrame, value_column: str = "close", group_by: str | None = None
    ) -> pd.DataFrame:
        """Calculate statistical summaries for data.

        Args:
            df: Input DataFrame.
            value_column: Column to calculate statistics for.
            group_by: Optional column to group by.

        Returns:
            DataFrame with statistical summaries.
        """
        if df.empty or value_column not in df.columns:
            logger.warning("Cannot calculate statistics on empty or invalid data")
            return pd.DataFrame()

        logger.info(f"Calculating statistics for {value_column}")

        if group_by and group_by in df.columns:
            stats = (
                df.groupby(group_by)[value_column]
                .agg(
                    [
                        ("count", "count"),
                        ("mean", "mean"),
                        ("std", "std"),
                        ("min", "min"),
                        ("25%", lambda x: x.quantile(0.25)),
                        ("50%", lambda x: x.quantile(0.50)),
                        ("75%", lambda x: x.quantile(0.75)),
                        ("max", "max"),
                    ]
                )
                .reset_index()
            )
        else:
            stats_dict = {
                "count": df[value_column].count(),
                "mean": df[value_column].mean(),
                "std": df[value_column].std(),
                "min": df[value_column].min(),
                "25%": df[value_column].quantile(0.25),
                "50%": df[value_column].quantile(0.50),
                "75%": df[value_column].quantile(0.75),
                "max": df[value_column].max(),
            }
            stats = pd.DataFrame([stats_dict])

        logger.info("Statistics calculated successfully")
        return stats

    def merge_with_master(
        self, data_df: pd.DataFrame, master_df: pd.DataFrame, on: str = "code", how: str = "left"
    ) -> pd.DataFrame:
        """Merge data with master information.

        Args:
            data_df: Main data DataFrame.
            master_df: Master data DataFrame (e.g., listed info).
            on: Column name to merge on.
            how: Type of merge (left, right, inner, outer).

        Returns:
            Merged DataFrame.
        """
        if data_df.empty:
            logger.warning("Cannot merge empty data DataFrame")
            return data_df

        if master_df.empty:
            logger.warning("Master DataFrame is empty, returning original data")
            return data_df

        logger.info(f"Merging {len(data_df)} records with master data")

        try:
            merged_df = data_df.merge(master_df, on=on, how=how)
            logger.info(f"Merge completed: {len(merged_df)} records")
            return merged_df
        except Exception as e:
            logger.error(f"Failed to merge DataFrames: {e}")
            return data_df

    def filter_by_date_range(
        self,
        df: pd.DataFrame,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        date_column: str = "date",
    ) -> pd.DataFrame:
        """Filter DataFrame by date range.

        Args:
            df: Input DataFrame.
            start_date: Start date (inclusive).
            end_date: End date (inclusive).
            date_column: Name of the date column.

        Returns:
            Filtered DataFrame.
        """
        if df.empty or date_column not in df.columns:
            return df

        initial_count = len(df)

        if start_date:
            df = df[df[date_column] >= start_date]

        if end_date:
            df = df[df[date_column] <= end_date]

        filtered_count = len(df)
        if filtered_count < initial_count:
            logger.info(f"Filtered by date range: {initial_count} -> {filtered_count} records")

        return df

    def filter_by_codes(
        self, df: pd.DataFrame, codes: list[str], code_column: str = "code"
    ) -> pd.DataFrame:
        """Filter DataFrame by stock codes.

        Args:
            df: Input DataFrame.
            codes: List of stock codes to keep.
            code_column: Name of the code column.

        Returns:
            Filtered DataFrame.
        """
        if df.empty or code_column not in df.columns:
            return df

        initial_count = len(df)
        df = df[df[code_column].isin(codes)]
        filtered_count = len(df)

        if filtered_count < initial_count:
            logger.info(f"Filtered by codes: {initial_count} -> {filtered_count} records")

        return df
