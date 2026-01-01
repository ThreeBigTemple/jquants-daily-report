"""Tests for data fetcher module."""

import pandas as pd
import pytest
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, MagicMock

from jquants_report.data.cache import CacheManager
from jquants_report.data.fetcher import DataFetcher


class TestDataFetcher:
    """Test cases for DataFetcher class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create CacheManager instance."""
        return CacheManager(temp_cache_dir, default_ttl_hours=24)

    @pytest.fixture
    def mock_api_client(self):
        """Create mock API client."""
        client = Mock()

        # Mock listed info response
        client.get_listed_info.return_value = {
            "info": [
                {"Code": "1301", "CompanyName": "Company A"},
                {"Code": "1302", "CompanyName": "Company B"},
            ]
        }

        # Mock daily quotes response
        client.get_daily_quotes.return_value = {
            "daily_quotes": [
                {
                    "Code": "1301",
                    "Date": "2024-01-15",
                    "Open": "100",
                    "Close": "105",
                    "Volume": "1000000",
                }
            ]
        }

        # Mock indices response
        client.get_indices.return_value = {
            "indices": [
                {
                    "Date": "2024-01-15",
                    "Code": "0000",
                    "IndexName": "TOPIX",
                    "Close": "2500",
                }
            ]
        }

        # Mock other responses
        client.get_topix.return_value = {"topix": []}
        client.get_trades_spec.return_value = {"trades_spec": []}
        client.get_margin_interest.return_value = {"margin_interest": []}
        client.get_short_selling.return_value = {"short_selling": []}
        client.get_statements.return_value = {"statements": []}
        client.get_announcement.return_value = {"announcement": []}

        return client

    @pytest.fixture
    def data_fetcher(self, mock_api_client, cache_manager):
        """Create DataFetcher instance."""
        return DataFetcher(mock_api_client, cache_manager)

    def test_fetch_listed_info(self, data_fetcher, mock_api_client):
        """Test fetching listed info."""
        result = data_fetcher.fetch_listed_info()

        assert not result.empty
        assert len(result) == 2
        assert "Code" in result.columns
        mock_api_client.get_listed_info.assert_called_once()

    def test_fetch_listed_info_with_cache(self, data_fetcher, mock_api_client):
        """Test fetching listed info uses cache."""
        # First call
        result1 = data_fetcher.fetch_listed_info()

        # Second call should use cache
        result2 = data_fetcher.fetch_listed_info()

        # API should only be called once
        assert mock_api_client.get_listed_info.call_count == 1
        assert len(result1) == len(result2)

    def test_fetch_listed_info_force_refresh(self, data_fetcher, mock_api_client):
        """Test force refresh bypasses cache."""
        # First call
        data_fetcher.fetch_listed_info()

        # Force refresh
        data_fetcher.fetch_listed_info(force_refresh=True)

        # API should be called twice
        assert mock_api_client.get_listed_info.call_count == 2

    def test_fetch_daily_quotes(self, data_fetcher, mock_api_client):
        """Test fetching daily quotes."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_daily_quotes(target_date)

        assert not result.empty
        mock_api_client.get_daily_quotes.assert_called_once()

    def test_fetch_daily_quotes_with_code(self, data_fetcher, mock_api_client):
        """Test fetching daily quotes for specific code."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_daily_quotes(target_date, code="1301")

        assert not result.empty
        mock_api_client.get_daily_quotes.assert_called_with(
            date="2024-01-15",
            code="1301"
        )

    def test_fetch_indices(self, data_fetcher, mock_api_client):
        """Test fetching index data."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_indices(target_date)

        assert not result.empty
        mock_api_client.get_indices.assert_called_once()

    def test_fetch_topix(self, data_fetcher, mock_api_client):
        """Test fetching TOPIX data."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_topix(target_date)

        assert isinstance(result, pd.DataFrame)
        mock_api_client.get_topix.assert_called_once()

    def test_fetch_trades_spec(self, data_fetcher, mock_api_client):
        """Test fetching trades spec data."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_trades_spec(target_date)

        assert isinstance(result, pd.DataFrame)
        mock_api_client.get_trades_spec.assert_called_once()

    def test_fetch_margin_interest(self, data_fetcher, mock_api_client):
        """Test fetching margin interest data (weekly)."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_margin_interest(target_date)

        assert isinstance(result, pd.DataFrame)
        mock_api_client.get_weekly_margin_trading.assert_called_once()

    def test_fetch_short_selling(self, data_fetcher, mock_api_client):
        """Test fetching short selling data."""
        target_date = date(2024, 1, 15)
        result = data_fetcher.fetch_short_selling(target_date)

        assert isinstance(result, pd.DataFrame)
        mock_api_client.get_short_selling.assert_called_once()

    def test_fetch_statements(self, data_fetcher, mock_api_client):
        """Test fetching financial statements."""
        result = data_fetcher.fetch_statements("1301")

        assert isinstance(result, pd.DataFrame)
        mock_api_client.get_statements.assert_called_with(code="1301")

    def test_fetch_announcement(self, data_fetcher, mock_api_client):
        """Test fetching announcement data."""
        result = data_fetcher.fetch_announcement()

        assert isinstance(result, pd.DataFrame)
        mock_api_client.get_announcement.assert_called_once()

    def test_fetch_date_range_quotes(self, data_fetcher, mock_api_client):
        """Test fetching quotes for date range using single API call."""
        start_date = date(2024, 1, 15)
        end_date = date(2024, 1, 17)

        result = data_fetcher.fetch_date_range_quotes(start_date, end_date)

        # Should be called once with from/to parameters (optimized)
        assert mock_api_client.get_daily_quotes.call_count == 1
        mock_api_client.get_daily_quotes.assert_called_with(
            code=None, from_date="2024-01-15", to_date="2024-01-17"
        )

    def test_api_error_handling(self, cache_manager):
        """Test handling of API errors."""
        # Create client that raises exception
        error_client = Mock()
        error_client.get_listed_info.side_effect = Exception("API Error")

        fetcher = DataFetcher(error_client, cache_manager)
        result = fetcher.fetch_listed_info()

        # Should return empty DataFrame on error
        assert result.empty

    def test_missing_api_method(self, cache_manager):
        """Test handling of missing API methods."""
        # Create client without expected method
        incomplete_client = Mock(spec=[])

        fetcher = DataFetcher(incomplete_client, cache_manager)
        result = fetcher.fetch_listed_info()

        # Should return empty DataFrame
        assert result.empty

    def test_rate_limiting(self, data_fetcher, mock_api_client):
        """Test rate limiting between API calls."""
        import time

        target_date = date(2024, 1, 15)

        # Make multiple consecutive calls
        start_time = time.time()
        data_fetcher.fetch_daily_quotes(target_date, force_refresh=True)
        data_fetcher.fetch_indices(target_date, force_refresh=True)
        end_time = time.time()

        # Should take at least MIN_REQUEST_INTERVAL seconds
        elapsed = end_time - start_time
        assert elapsed >= DataFetcher.MIN_REQUEST_INTERVAL

    def test_different_response_formats(self, cache_manager):
        """Test handling different API response formats."""
        # Test list response
        client = Mock()
        client.get_listed_info.return_value = [
            {"Code": "1301"},
            {"Code": "1302"},
        ]

        fetcher = DataFetcher(client, cache_manager)
        result = fetcher.fetch_listed_info()
        assert len(result) == 2

        # Test single dict response
        client.get_listed_info.return_value = {"Code": "1301"}
        fetcher = DataFetcher(client, cache_manager)
        result = fetcher.fetch_listed_info(force_refresh=True)
        assert len(result) == 1

    def test_cache_key_uniqueness(self, data_fetcher):
        """Test that different parameters create different cache keys."""
        target_date = date(2024, 1, 15)

        # Fetch for different codes
        data_fetcher.fetch_daily_quotes(target_date, code="1301")
        data_fetcher.fetch_daily_quotes(target_date, code="1302")

        # Both should be cached separately
        cache1 = data_fetcher.cache.get("daily_quotes_2024-01-15_1301")
        cache2 = data_fetcher.cache.get("daily_quotes_2024-01-15_1302")

        assert cache1 is not None
        assert cache2 is not None

    def test_empty_api_response(self, cache_manager):
        """Test handling of empty API responses."""
        client = Mock()
        client.get_daily_quotes.return_value = None

        fetcher = DataFetcher(client, cache_manager)
        result = fetcher.fetch_daily_quotes(date(2024, 1, 15))

        assert result.empty
