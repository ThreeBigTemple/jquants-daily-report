"""Data fetcher for J-Quants API.

This module handles fetching data from J-Quants API with caching support.
Implements rate limiting, retry logic, and differential updates.
"""

import logging
import time
from datetime import date, timedelta
from typing import Any

import pandas as pd

from jquants_report.data.cache import CacheManager

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetches and caches data from J-Quants API.

    Implements intelligent caching, rate limiting, and retry mechanisms
    to efficiently retrieve market data.
    """

    # Rate limiting - 1 second between API calls
    MIN_REQUEST_INTERVAL = 1.0

    def __init__(self, api_client: Any, cache_manager: CacheManager):
        """Initialize DataFetcher.

        Args:
            api_client: Instance of JQuantsClient for API access.
            cache_manager: Instance of CacheManager for data caching.
        """
        self.client = api_client
        self.cache = cache_manager
        self._last_request_time: float = 0.0

    def _rate_limit(self) -> None:
        """Enforce rate limiting between API requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            sleep_time = self.MIN_REQUEST_INTERVAL - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    def _make_api_call(self, method_name: str, *args: Any, **kwargs: Any) -> dict[str, Any] | None:
        """Make an API call with rate limiting and error handling.

        Args:
            method_name: Name of the API client method to call.
            *args: Positional arguments for the method.
            **kwargs: Keyword arguments for the method.

        Returns:
            API response data or None if failed.
        """
        self._rate_limit()

        try:
            method = getattr(self.client, method_name)
            response = method(*args, **kwargs)
            logger.debug(f"API call successful: {method_name}")
            return response
        except AttributeError:
            logger.error(f"API method not found: {method_name}")
            return None
        except Exception as e:
            logger.error(f"API call failed ({method_name}): {e}")
            return None

    def fetch_listed_info(self, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch listed company information.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing listed company information.
        """
        cache_key = "listed_info"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info("Fetching listed company information")
        response = self._make_api_call("get_listed_info")

        if response is None:
            logger.warning("Failed to fetch listed info, returning empty DataFrame")
            return pd.DataFrame()

        try:
            # JQuantsClient already returns DataFrame
            if isinstance(response, pd.DataFrame):
                df = response
            elif isinstance(response, dict) and "info" in response:
                df = pd.DataFrame(response["info"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            # Cache for 24 hours (master data changes infrequently)
            if not df.empty:
                self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process listed info: {e}")
            return pd.DataFrame()

    def fetch_daily_quotes(
        self, target_date: date, code: str | None = None, force_refresh: bool = False
    ) -> pd.DataFrame:
        """Fetch daily stock quotes.

        Args:
            target_date: Date for which to fetch quotes.
            code: Optional stock code. If None, fetches all stocks.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing daily quotes.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"daily_quotes_{date_str}"
        if code:
            cache_key += f"_{code}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info(f"Fetching daily quotes for {date_str}" + (f" (code: {code})" if code else ""))
        response = self._make_api_call("get_daily_quotes", date=date_str, code=code)

        if response is None:
            logger.warning("Failed to fetch daily quotes, returning empty DataFrame")
            return pd.DataFrame()

        try:
            # JQuantsClient already returns DataFrame
            if isinstance(response, pd.DataFrame):
                df = response
            elif isinstance(response, dict) and "daily_quotes" in response:
                df = pd.DataFrame(response["daily_quotes"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            # Cache for 24 hours
            if not df.empty:
                self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process daily quotes: {e}")
            return pd.DataFrame()

    def fetch_indices(self, target_date: date, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch index data (NIKKEI, TOPIX, etc.).

        Args:
            target_date: Date for which to fetch indices.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing index data.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"indices_{date_str}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info(f"Fetching index data for {date_str}")
        response = self._make_api_call("get_indices", date=date_str)

        if response is None:
            logger.warning("Failed to fetch indices, returning empty DataFrame")
            return pd.DataFrame()

        try:
            # JQuantsClient already returns DataFrame
            if isinstance(response, pd.DataFrame):
                df = response
            elif isinstance(response, dict) and "indices" in response:
                df = pd.DataFrame(response["indices"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            if not df.empty:
                self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process indices: {e}")
            return pd.DataFrame()

    def fetch_topix(self, target_date: date, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch TOPIX data.

        Args:
            target_date: Date for which to fetch TOPIX data.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing TOPIX data.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"topix_{date_str}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info(f"Fetching TOPIX data for {date_str}")
        response = self._make_api_call("get_topix", date=date_str)

        if response is None:
            logger.warning("Failed to fetch TOPIX, returning empty DataFrame")
            return pd.DataFrame()

        try:
            if isinstance(response, dict) and "topix" in response:
                df = pd.DataFrame(response["topix"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process TOPIX: {e}")
            return pd.DataFrame()

    def fetch_trades_spec(self, target_date: date, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch trading by investor type data.

        Args:
            target_date: Date for which to fetch data.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing investor type trading data.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"trades_spec_{date_str}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info(f"Fetching trades spec for {date_str}")
        response = self._make_api_call("get_trades_spec", date=date_str)

        if response is None:
            logger.warning("Failed to fetch trades spec, returning empty DataFrame")
            return pd.DataFrame()

        try:
            if isinstance(response, dict) and "trades_spec" in response:
                df = pd.DataFrame(response["trades_spec"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process trades spec: {e}")
            return pd.DataFrame()

    def fetch_margin_interest(self, target_date: date, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch weekly margin trading balance data.

        Args:
            target_date: Date for which to fetch data.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing margin trading balance.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"margin_interest_{date_str}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        # Use weekly margin trading data (信用残高は週次発表)
        logger.info(f"Fetching weekly margin interest for {date_str}")
        response = self._make_api_call("get_weekly_margin_trading", date=date_str)

        if response is None:
            logger.warning("Failed to fetch margin interest, returning empty DataFrame")
            return pd.DataFrame()

        try:
            # JQuantsClient returns DataFrame directly
            if isinstance(response, pd.DataFrame):
                df = response
            elif isinstance(response, dict) and "weekly_margin_interest" in response:
                df = pd.DataFrame(response["weekly_margin_interest"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            # Normalize column names for compatibility
            column_mapping = {
                "MarginBuyingBalance": "MarginBuyBalance",
                "MarginSellingBalance": "MarginSellBalance",
                "MarginBuyingNewBalance": "MarginBuyValue",
                "MarginSellingNewBalance": "MarginSellValue",
            }
            df = df.rename(columns=column_mapping)

            if not df.empty:
                self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process margin interest: {e}")
            return pd.DataFrame()

    def fetch_short_selling(self, target_date: date, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch short selling ratio data.

        Args:
            target_date: Date for which to fetch data.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing short selling ratio.
        """
        date_str = target_date.strftime("%Y-%m-%d")
        cache_key = f"short_selling_{date_str}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info(f"Fetching short selling for {date_str}")
        response = self._make_api_call("get_short_selling", date=date_str)

        if response is None:
            logger.warning("Failed to fetch short selling, returning empty DataFrame")
            return pd.DataFrame()

        try:
            # JQuantsClient returns DataFrame directly
            if isinstance(response, pd.DataFrame):
                df = response
            elif isinstance(response, dict) and "short_selling" in response:
                df = pd.DataFrame(response["short_selling"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            if not df.empty:
                self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process short selling: {e}")
            return pd.DataFrame()

    def fetch_statements(self, code: str, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch financial statements for a specific company.

        Args:
            code: Stock code.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing financial statements.
        """
        cache_key = f"statements_{code}"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info(f"Fetching statements for {code}")
        response = self._make_api_call("get_statements", code=code)

        if response is None:
            logger.warning(f"Failed to fetch statements for {code}, returning empty DataFrame")
            return pd.DataFrame()

        try:
            if isinstance(response, dict) and "statements" in response:
                df = pd.DataFrame(response["statements"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            # Cache for 24 hours
            self.cache.set(cache_key, df, ttl_hours=24)
            return df

        except Exception as e:
            logger.error(f"Failed to process statements for {code}: {e}")
            return pd.DataFrame()

    def fetch_announcement(self, force_refresh: bool = False) -> pd.DataFrame:
        """Fetch earnings announcement schedule.

        Args:
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing announcement schedule.
        """
        cache_key = "announcement"

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        logger.info("Fetching earnings announcement schedule")
        response = self._make_api_call("get_announcement")

        if response is None:
            logger.warning("Failed to fetch announcement, returning empty DataFrame")
            return pd.DataFrame()

        try:
            if isinstance(response, dict) and "announcement" in response:
                df = pd.DataFrame(response["announcement"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame([response])

            # Cache for 6 hours (updates more frequently)
            self.cache.set(cache_key, df, ttl_hours=6)
            return df

        except Exception as e:
            logger.error(f"Failed to process announcement: {e}")
            return pd.DataFrame()

    def fetch_date_range_quotes(
        self, start_date: date, end_date: date, code: str | None = None, force_refresh: bool = False
    ) -> pd.DataFrame:
        """Fetch daily quotes for a date range using single API call.

        Args:
            start_date: Start date of the range.
            end_date: End date of the range.
            code: Optional stock code. If None, fetches all stocks.
            force_refresh: If True, bypass cache and fetch fresh data.

        Returns:
            DataFrame containing quotes for the date range.
        """
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")
        cache_key = f"quotes_range_{start_str}_{end_str}" + (f"_{code}" if code else "")

        if not force_refresh:
            cached_data = self.cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Using cached data for {start_str} to {end_str}")
                return cached_data

        logger.info(
            f"Fetching quotes from {start_date} to {end_date}"
            + (f" for code {code}" if code else " (all stocks)")
        )

        # Use single API call with from/to parameters
        response = self._make_api_call(
            "get_daily_quotes",
            code=code,
            from_date=start_str,
            to_date=end_str,
        )

        if response is None:
            logger.warning("Failed to fetch date range quotes")
            return pd.DataFrame()

        try:
            if isinstance(response, pd.DataFrame):
                df = response
            elif isinstance(response, dict) and "daily_quotes" in response:
                df = pd.DataFrame(response["daily_quotes"])
            elif isinstance(response, list):
                df = pd.DataFrame(response)
            else:
                df = pd.DataFrame()

            if not df.empty:
                self.cache.set(cache_key, df, ttl_hours=24)
                logger.info(f"Fetched {len(df)} records for date range")

            return df

        except Exception as e:
            logger.error(f"Failed to process date range quotes: {e}")
            return pd.DataFrame()
