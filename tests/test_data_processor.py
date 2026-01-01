"""Tests for data processor module."""

import pandas as pd
import pytest
from datetime import datetime

from jquants_report.data.processor import DataProcessor


class TestDataProcessor:
    """Test cases for DataProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create DataProcessor instance."""
        return DataProcessor()

    @pytest.fixture
    def sample_daily_quotes(self):
        """Create sample daily quotes data."""
        return pd.DataFrame({
            "Code": ["1301", "1301", "1302"],
            "Date": ["2024-01-15", "2024-01-16", "2024-01-15"],
            "Open": ["100", "102", "200"],
            "High": ["105", "108", "210"],
            "Low": ["98", "101", "195"],
            "Close": ["103", "106", "205"],
            "Volume": ["1000000", "1200000", "500000"],
        })

    @pytest.fixture
    def sample_listed_info(self):
        """Create sample listed info data."""
        return pd.DataFrame({
            "Code": ["1301", "1302", "1301"],  # Duplicate to test deduplication
            "CompanyName": ["Company A", "Company B", "Company A Updated"],
            "Sector17Code": ["1", "2", "1"],
            "MarketCode": ["0111", "0111", "0111"],
        })

    def test_process_daily_quotes(self, processor, sample_daily_quotes):
        """Test processing daily quotes data."""
        result = processor.process_daily_quotes(sample_daily_quotes)

        # Check column standardization
        assert "code" in result.columns
        assert "date" in result.columns
        assert "close" in result.columns

        # Check data types
        assert pd.api.types.is_datetime64_any_dtype(result["date"])
        assert pd.api.types.is_numeric_dtype(result["close"])

        # Check derived columns
        assert "price_change" in result.columns
        assert "price_change_pct" in result.columns

        # Check sorting
        assert result["code"].tolist() == ["1301", "1301", "1302"]

    def test_process_daily_quotes_empty(self, processor):
        """Test processing empty daily quotes data."""
        empty_df = pd.DataFrame()
        result = processor.process_daily_quotes(empty_df)
        assert result.empty

    def test_process_listed_info(self, processor, sample_listed_info):
        """Test processing listed info data."""
        result = processor.process_listed_info(sample_listed_info)

        # Check column standardization
        assert "code" in result.columns
        assert "company_name" in result.columns

        # Check deduplication (should keep last)
        assert len(result) == 2
        company_a = result[result["code"] == "1301"]
        assert company_a["company_name"].iloc[0] == "Company A Updated"

    def test_process_indices(self, processor):
        """Test processing index data."""
        sample_data = pd.DataFrame({
            "Date": ["2024-01-15", "2024-01-16"],
            "Code": ["0000", "0000"],
            "IndexName": ["TOPIX", "TOPIX"],
            "Open": ["2500.0", "2520.0"],
            "Close": ["2510.0", "2530.0"],
        })

        result = processor.process_indices(sample_data)

        # Check derived columns
        assert "change" in result.columns
        assert "change_pct" in result.columns

        # Check calculations
        assert result["change"].iloc[0] == 10.0
        assert abs(result["change_pct"].iloc[0] - 0.4) < 0.01

    def test_calculate_statistics(self, processor, sample_daily_quotes):
        """Test statistics calculation."""
        processed_df = processor.process_daily_quotes(sample_daily_quotes)
        stats = processor.calculate_statistics(processed_df, value_column="close")

        assert "count" in stats.columns
        assert "mean" in stats.columns
        assert "std" in stats.columns
        assert stats["count"].iloc[0] == 3

    def test_calculate_statistics_grouped(self, processor, sample_daily_quotes):
        """Test grouped statistics calculation."""
        processed_df = processor.process_daily_quotes(sample_daily_quotes)
        stats = processor.calculate_statistics(
            processed_df,
            value_column="close",
            group_by="code"
        )

        assert len(stats) == 2  # Two unique codes
        assert "code" in stats.columns

    def test_merge_with_master(self, processor, sample_daily_quotes, sample_listed_info):
        """Test merging with master data."""
        quotes_df = processor.process_daily_quotes(sample_daily_quotes)
        master_df = processor.process_listed_info(sample_listed_info)

        merged = processor.merge_with_master(quotes_df, master_df, on="code")

        assert "company_name" in merged.columns
        assert len(merged) == len(quotes_df)

    def test_filter_by_date_range(self, processor, sample_daily_quotes):
        """Test date range filtering."""
        processed_df = processor.process_daily_quotes(sample_daily_quotes)

        filtered = processor.filter_by_date_range(
            processed_df,
            start_date=datetime(2024, 1, 16),
            date_column="date"
        )

        assert len(filtered) == 1
        assert filtered["date"].iloc[0] == pd.Timestamp("2024-01-16")

    def test_filter_by_codes(self, processor, sample_daily_quotes):
        """Test filtering by stock codes."""
        processed_df = processor.process_daily_quotes(sample_daily_quotes)

        filtered = processor.filter_by_codes(
            processed_df,
            codes=["1301"],
            code_column="code"
        )

        assert len(filtered) == 2
        assert all(filtered["code"] == "1301")

    def test_process_margin_interest(self, processor):
        """Test processing margin interest data."""
        sample_data = pd.DataFrame({
            "Code": ["1301", "1302"],
            "Date": ["2024-01-15", "2024-01-15"],
            "MarginBuy": ["1000", "2000"],
            "MarginSell": ["500", "800"],
        })

        result = processor.process_margin_interest(sample_data)

        assert "code" in result.columns
        assert "margin_buy" in result.columns
        assert pd.api.types.is_numeric_dtype(result["margin_buy"])

    def test_process_short_selling(self, processor):
        """Test processing short selling data."""
        sample_data = pd.DataFrame({
            "Code": ["1301", "1302"],
            "Date": ["2024-01-15", "2024-01-15"],
            "ShortSellingVolume": ["10000", "20000"],
            "TotalVolume": ["100000", "150000"],
        })

        result = processor.process_short_selling(sample_data)

        assert "short_selling_ratio" in result.columns
        assert result["short_selling_ratio"].iloc[0] == 10.0
