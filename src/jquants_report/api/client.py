"""J-Quants API client with comprehensive endpoint access.

This module provides the main API client for interacting with J-Quants API,
including rate limiting, automatic retry, and error handling.
"""

import logging
import time
from typing import Any

import pandas as pd
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from jquants_report.api.auth import AuthenticationError, JQuantsAuthenticator
from jquants_report.api.endpoints import JQuantsEndpoints, build_query_params

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Base exception for API errors."""

    pass


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""

    pass


class NotFoundError(APIError):
    """Raised when requested resource is not found."""

    pass


class JQuantsClient:
    """Client for J-Quants API with comprehensive endpoint access.

    This client provides:
    - Automatic authentication token management
    - Rate limiting (1 request per second)
    - Automatic retry with exponential backoff
    - Type-safe endpoint access
    - DataFrame conversion for tabular data

    Attributes:
        authenticator: Authentication handler.
        base_url: Base URL for the API.
        rate_limit_delay: Minimum seconds between requests (default: 1.0).
        last_request_time: Timestamp of last API request.
    """

    def __init__(
        self,
        email: str,
        password: str,
        refresh_token: str | None = None,
        base_url: str = "https://api.jquants.com/v1",
        rate_limit_delay: float = 1.0,
    ) -> None:
        """Initialize the J-Quants API client.

        Args:
            email: J-Quants account email.
            password: J-Quants account password.
            refresh_token: Optional pre-existing refresh token.
            base_url: Base URL for J-Quants API.
            rate_limit_delay: Minimum seconds between API requests.
        """
        self.authenticator = JQuantsAuthenticator(
            base_url=base_url,
            email=email,
            password=password,
            refresh_token=refresh_token,
        )
        self.base_url = base_url.rstrip("/")
        self.rate_limit_delay = rate_limit_delay
        self._last_request_time: float = 0.0

    def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting by sleeping if necessary."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        self._last_request_time = time.time()

    @retry(
        retry=retry_if_exception_type((requests.RequestException, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def _make_request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        method: str = "GET",
    ) -> dict[str, Any]:
        """Make an authenticated API request with retry logic.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.
            method: HTTP method (default: GET).

        Returns:
            JSON response as dictionary.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
            NotFoundError: If resource is not found.
            APIError: For other API errors.
        """
        self._enforce_rate_limit()

        url = f"{self.base_url}{endpoint}"
        headers = self.authenticator.get_auth_headers()

        logger.debug(f"Making {method} request to {endpoint} with params: {params}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                timeout=30,
            )

            # Handle specific HTTP status codes
            if response.status_code == 401:
                logger.warning("Authentication failed, invalidating tokens")
                self.authenticator.invalidate_tokens()
                raise AuthenticationError("Authentication failed (401)")
            elif response.status_code == 404:
                raise NotFoundError(f"Resource not found: {endpoint}")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            elif response.status_code >= 500:
                raise APIError(f"Server error: {response.status_code}")

            response.raise_for_status()

        except requests.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise APIError(f"Request failed: {e}") from e

        try:
            return response.json()
        except ValueError as e:
            raise APIError(f"Invalid JSON response: {e}") from e

    def _to_dataframe(self, data: dict[str, Any], key: str = "data") -> pd.DataFrame:
        """Convert API response to pandas DataFrame.

        Args:
            data: API response dictionary.
            key: Key containing the data array (default: "data").

        Returns:
            DataFrame containing the data, or empty DataFrame if no data.
        """
        if key not in data or not data[key]:
            logger.warning(f"No data found in response for key: {key}")
            return pd.DataFrame()

        return pd.DataFrame(data[key])

    # ==================== Listed Information ====================

    def get_listed_info(self, code: str | None = None, date: str | None = None) -> pd.DataFrame:
        """Get information about listed companies.

        Args:
            code: Stock code (4-digit or 5-digit string).
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing listed company information.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.LISTED_INFO.path, params)
        return self._to_dataframe(response, "info")

    def get_listed_sections(self, code: str | None = None) -> pd.DataFrame:
        """Get section information for listed companies.

        Args:
            code: Stock code.

        Returns:
            DataFrame containing section information.
        """
        params = build_query_params(code=code)
        response = self._make_request(JQuantsEndpoints.LISTED_SECTIONS.path, params)
        return self._to_dataframe(response, "sections")

    # ==================== Price Data ====================

    def get_daily_quotes(
        self,
        code: str | None = None,
        date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> pd.DataFrame:
        """Get daily stock quotes (OHLCV data).

        Args:
            code: Stock code.
            date: Specific date in YYYYMMDD or YYYY-MM-DD format.
            from_date: Start date for range query.
            to_date: End date for range query.

        Returns:
            DataFrame containing daily quotes.
        """
        params = build_query_params(
            code=code,
            date=date,
            **{"from": from_date, "to": to_date} if from_date or to_date else {},
        )
        response = self._make_request(JQuantsEndpoints.PRICES_DAILY_QUOTES.path, params)
        return self._to_dataframe(response, "daily_quotes")

    def get_prices_am(
        self,
        code: str | None = None,
        date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> pd.DataFrame:
        """Get morning session prices.

        Args:
            code: Stock code.
            date: Specific date in YYYYMMDD or YYYY-MM-DD format.
            from_date: Start date for range query.
            to_date: End date for range query.

        Returns:
            DataFrame containing morning session prices.
        """
        params = build_query_params(
            code=code,
            date=date,
            **{"from": from_date, "to": to_date} if from_date or to_date else {},
        )
        response = self._make_request(JQuantsEndpoints.PRICES_AM.path, params)
        return self._to_dataframe(response, "prices_am")

    # ==================== Financial Data ====================

    def get_financial_statements(
        self, code: str | None = None, date: str | None = None
    ) -> pd.DataFrame:
        """Get financial statements data.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing financial statements.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.FINS_STATEMENTS.path, params)
        return self._to_dataframe(response, "statements")

    def get_financial_announcement(
        self, code: str | None = None, date: str | None = None
    ) -> pd.DataFrame:
        """Get financial announcement schedules.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing financial announcement schedules.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.FINS_ANNOUNCEMENT.path, params)
        return self._to_dataframe(response, "announcement")

    def get_dividend_info(self, code: str | None = None, date: str | None = None) -> pd.DataFrame:
        """Get dividend information.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing dividend information.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.FINS_DIVIDEND.path, params)
        return self._to_dataframe(response, "dividend")

    # ==================== Index Data ====================

    def get_indices(
        self,
        code: str | None = None,
        date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> pd.DataFrame:
        """Get index data.

        Args:
            code: Index code.
            date: Specific date in YYYYMMDD or YYYY-MM-DD format.
            from_date: Start date for range query.
            to_date: End date for range query.

        Returns:
            DataFrame containing index data.
        """
        params = build_query_params(
            code=code,
            date=date,
            **{"from": from_date, "to": to_date} if from_date or to_date else {},
        )
        response = self._make_request(JQuantsEndpoints.INDICES.path, params)
        return self._to_dataframe(response, "indices")

    def get_topix_composition(
        self, code: str | None = None, date: str | None = None
    ) -> pd.DataFrame:
        """Get TOPIX index composition and weights.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing TOPIX composition.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.INDICES_TOPIX.path, params)
        return self._to_dataframe(response, "topix")

    # ==================== Market Data ====================

    def get_trades_by_investor_type(
        self,
        section: str | None = None,
        date: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> pd.DataFrame:
        """Get trading by investor type (institutional, foreign, etc.).

        Args:
            section: Market section code.
            date: Specific date in YYYYMMDD or YYYY-MM-DD format.
            from_date: Start date for range query.
            to_date: End date for range query.

        Returns:
            DataFrame containing trading by investor type.
        """
        params = build_query_params(
            section=section,
            date=date,
            **{"from": from_date, "to": to_date} if from_date or to_date else {},
        )
        response = self._make_request(JQuantsEndpoints.MARKETS_TRADES_SPEC.path, params)
        return self._to_dataframe(response, "trades_spec")

    def get_short_selling(
        self,
        code: str | None = None,
        sector33code: str | None = None,
        date: str | None = None,
    ) -> pd.DataFrame:
        """Get short selling data.

        Args:
            code: Stock code.
            sector33code: Sector code (33 sectors).
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing short selling data.
        """
        params = build_query_params(code=code, sector33code=sector33code, date=date)
        response = self._make_request(JQuantsEndpoints.MARKETS_SHORT_SELLING.path, params)
        return self._to_dataframe(response, "short_selling")

    def get_margin_trading(self, code: str | None = None, date: str | None = None) -> pd.DataFrame:
        """Get margin trading data.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing margin trading data.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.MARKETS_MARGIN_INTEREST.path, params)
        return self._to_dataframe(response, "margin_interest")

    def get_market_breakdown(self, date: str | None = None) -> pd.DataFrame:
        """Get market breakdown by value/volume.

        Args:
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing market breakdown.
        """
        params = build_query_params(date=date)
        response = self._make_request(JQuantsEndpoints.MARKETS_BREAKDOWN.path, params)
        return self._to_dataframe(response, "breakdown")

    def get_weekly_margin_trading(
        self, code: str | None = None, date: str | None = None
    ) -> pd.DataFrame:
        """Get weekly margin trading data.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing weekly margin trading data.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.MARKETS_WEEKLY_MARGIN_INTEREST.path, params)
        return self._to_dataframe(response, "weekly_margin_interest")

    # ==================== Options Data ====================

    def get_index_option(self, date: str | None = None) -> pd.DataFrame:
        """Get index option data.

        Args:
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing index option data.
        """
        params = build_query_params(date=date)
        response = self._make_request(JQuantsEndpoints.OPTION_INDEX_OPTION.path, params)
        return self._to_dataframe(response, "index_option")

    # ==================== Futures Data ====================

    def get_index_futures(self, date: str | None = None) -> pd.DataFrame:
        """Get index futures data.

        Args:
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing index futures data.
        """
        params = build_query_params(date=date)
        response = self._make_request(JQuantsEndpoints.FUTURES_INDEX_FUTURES.path, params)
        return self._to_dataframe(response, "index_futures")

    # ==================== Disclosure Data ====================

    def get_tdnet_disclosure(
        self, code: str | None = None, date: str | None = None
    ) -> pd.DataFrame:
        """Get TDnet disclosure information.

        Args:
            code: Stock code.
            date: Date in YYYYMMDD or YYYY-MM-DD format.

        Returns:
            DataFrame containing TDnet disclosure information.
        """
        params = build_query_params(code=code, date=date)
        response = self._make_request(JQuantsEndpoints.DISCLOSURE_TDNET.path, params)
        return self._to_dataframe(response, "tdnet")

    # ==================== Utility Methods ====================

    def get_refresh_token(self) -> str:
        """Get the current refresh token.

        Useful for saving the refresh token to avoid repeated email/password auth.

        Returns:
            The current refresh token string.
        """
        return self.authenticator.get_refresh_token()

    def clear_cache(self) -> None:
        """Clear all cached authentication tokens."""
        self.authenticator.clear_all_tokens()
