"""Unit tests for J-Quants API client.

This module contains comprehensive tests for:
- Authentication flow (refresh token, ID token)
- API client methods
- Rate limiting
- Error handling and retry logic
"""

import time
from unittest.mock import MagicMock, Mock, patch

import pandas as pd
import pytest
import requests
import responses

from jquants_report.api.auth import (
    AuthenticationError,
    JQuantsAuthenticator,
    TokenExpiredError,
    TokenInfo,
)
from jquants_report.api.client import (
    APIError,
    JQuantsClient,
    NotFoundError,
    RateLimitError,
)
from jquants_report.api.endpoints import JQuantsEndpoints, build_query_params


# ==================== Fixtures ====================


@pytest.fixture
def mock_email() -> str:
    """Return mock email for testing."""
    return "test@example.com"


@pytest.fixture
def mock_password() -> str:
    """Return mock password for testing."""
    return "test_password"


@pytest.fixture
def mock_refresh_token() -> str:
    """Return mock refresh token for testing."""
    return "mock_refresh_token_123"


@pytest.fixture
def mock_id_token() -> str:
    """Return mock ID token for testing."""
    return "mock_id_token_456"


@pytest.fixture
def base_url() -> str:
    """Return base URL for testing."""
    return "https://api.jquants.com/v1"


@pytest.fixture
def authenticator(
    mock_email: str, mock_password: str, base_url: str
) -> JQuantsAuthenticator:
    """Create authenticator instance for testing."""
    return JQuantsAuthenticator(
        base_url=base_url,
        email=mock_email,
        password=mock_password,
    )


@pytest.fixture
def client(mock_email: str, mock_password: str, base_url: str) -> JQuantsClient:
    """Create client instance for testing."""
    return JQuantsClient(
        email=mock_email,
        password=mock_password,
        base_url=base_url,
        rate_limit_delay=0.1,  # Shorter delay for testing
    )


# ==================== TokenInfo Tests ====================


class TestTokenInfo:
    """Test TokenInfo class."""

    def test_token_info_creation(self) -> None:
        """Test creating a TokenInfo instance."""
        token = TokenInfo(token="test_token", expires_at=time.time() + 3600)
        assert token.token == "test_token"
        assert token.expires_at > time.time()

    def test_is_expired_not_expired(self) -> None:
        """Test that a fresh token is not expired."""
        token = TokenInfo(token="test_token", expires_at=time.time() + 3600)
        assert not token.is_expired()

    def test_is_expired_expired(self) -> None:
        """Test that an expired token is detected."""
        token = TokenInfo(token="test_token", expires_at=time.time() - 100)
        assert token.is_expired()

    def test_is_expired_with_buffer(self) -> None:
        """Test expiration check with buffer."""
        # Token expires in 100 seconds
        token = TokenInfo(token="test_token", expires_at=time.time() + 100)
        # With 300 second buffer, should be considered expired
        assert token.is_expired(buffer_seconds=300)
        # With 50 second buffer, should not be expired
        assert not token.is_expired(buffer_seconds=50)


# ==================== JQuantsAuthenticator Tests ====================


class TestJQuantsAuthenticator:
    """Test JQuantsAuthenticator class."""

    @responses.activate
    def test_get_refresh_token_success(
        self, authenticator: JQuantsAuthenticator, mock_refresh_token: str
    ) -> None:
        """Test successful refresh token acquisition."""
        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_user",
            json={"refreshToken": mock_refresh_token},
            status=200,
        )

        token = authenticator.get_refresh_token()
        assert token == mock_refresh_token
        assert authenticator._refresh_token == mock_refresh_token

    @responses.activate
    def test_get_refresh_token_uses_cached(
        self, authenticator: JQuantsAuthenticator, mock_refresh_token: str
    ) -> None:
        """Test that cached refresh token is used."""
        authenticator._refresh_token = mock_refresh_token
        token = authenticator.get_refresh_token()
        assert token == mock_refresh_token
        # No HTTP request should be made

    @responses.activate
    def test_get_refresh_token_failure(self, authenticator: JQuantsAuthenticator) -> None:
        """Test refresh token acquisition failure."""
        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_user",
            json={"error": "Invalid credentials"},
            status=401,
        )

        with pytest.raises(AuthenticationError):
            authenticator.get_refresh_token()

    @responses.activate
    def test_get_refresh_token_missing_in_response(
        self, authenticator: JQuantsAuthenticator
    ) -> None:
        """Test handling of missing refresh token in response."""
        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_user",
            json={"some_other_field": "value"},
            status=200,
        )

        with pytest.raises(AuthenticationError, match="Refresh token not found"):
            authenticator.get_refresh_token()

    @responses.activate
    def test_get_id_token_success(
        self,
        authenticator: JQuantsAuthenticator,
        mock_refresh_token: str,
        mock_id_token: str,
    ) -> None:
        """Test successful ID token acquisition."""
        authenticator._refresh_token = mock_refresh_token

        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_refresh",
            json={"idToken": mock_id_token},
            status=200,
        )

        token = authenticator.get_id_token()
        assert token == mock_id_token
        assert authenticator._id_token is not None
        assert authenticator._id_token.token == mock_id_token

    @responses.activate
    def test_get_id_token_uses_cached(
        self, authenticator: JQuantsAuthenticator, mock_id_token: str
    ) -> None:
        """Test that cached ID token is used if not expired."""
        authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        token = authenticator.get_id_token()
        assert token == mock_id_token
        # No HTTP request should be made

    @responses.activate
    def test_get_id_token_refreshes_when_expired(
        self,
        authenticator: JQuantsAuthenticator,
        mock_refresh_token: str,
        mock_id_token: str,
    ) -> None:
        """Test that expired ID token is refreshed."""
        authenticator._refresh_token = mock_refresh_token
        authenticator._id_token = TokenInfo(
            token="old_token", expires_at=time.time() - 100
        )

        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_refresh",
            json={"idToken": mock_id_token},
            status=200,
        )

        token = authenticator.get_id_token()
        assert token == mock_id_token
        assert authenticator._id_token.token == mock_id_token

    @responses.activate
    def test_get_id_token_force_refresh(
        self,
        authenticator: JQuantsAuthenticator,
        mock_refresh_token: str,
        mock_id_token: str,
    ) -> None:
        """Test forcing ID token refresh."""
        authenticator._refresh_token = mock_refresh_token
        authenticator._id_token = TokenInfo(
            token="old_token", expires_at=time.time() + 3600
        )

        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_refresh",
            json={"idToken": mock_id_token},
            status=200,
        )

        token = authenticator.get_id_token(force_refresh=True)
        assert token == mock_id_token

    @responses.activate
    def test_get_auth_headers(
        self,
        authenticator: JQuantsAuthenticator,
        mock_refresh_token: str,
        mock_id_token: str,
    ) -> None:
        """Test getting authentication headers."""
        authenticator._refresh_token = mock_refresh_token

        responses.add(
            responses.POST,
            f"{authenticator.base_url}/token/auth_refresh",
            json={"idToken": mock_id_token},
            status=200,
        )

        headers = authenticator.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == f"Bearer {mock_id_token}"

    def test_invalidate_tokens(
        self, authenticator: JQuantsAuthenticator, mock_id_token: str
    ) -> None:
        """Test invalidating cached tokens."""
        authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )
        authenticator.invalidate_tokens()
        assert authenticator._id_token is None

    def test_clear_all_tokens(
        self,
        authenticator: JQuantsAuthenticator,
        mock_refresh_token: str,
        mock_id_token: str,
    ) -> None:
        """Test clearing all tokens."""
        authenticator._refresh_token = mock_refresh_token
        authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        authenticator.clear_all_tokens()
        assert authenticator._refresh_token is None
        assert authenticator._id_token is None


# ==================== Endpoint Tests ====================


class TestEndpoints:
    """Test endpoint definitions and utilities."""

    def test_build_query_params_filters_none(self) -> None:
        """Test that None values are filtered out."""
        params = build_query_params(code="27800", date="20240115", limit=None)
        assert params == {"code": "27800", "date": "20240115"}

    def test_build_query_params_converts_to_string(self) -> None:
        """Test that values are converted to strings."""
        params = build_query_params(code=27800, limit=100)
        assert params == {"code": "27800", "limit": "100"}

    def test_build_query_params_empty(self) -> None:
        """Test building empty query params."""
        params = build_query_params()
        assert params == {}

    def test_get_all_endpoints(self) -> None:
        """Test retrieving all endpoints."""
        endpoints = JQuantsEndpoints.get_all_endpoints()
        assert len(endpoints) > 0
        assert "LISTED_INFO" in endpoints
        assert "PRICES_DAILY_QUOTES" in endpoints

    def test_get_endpoint_by_path(self) -> None:
        """Test finding endpoint by path."""
        endpoint = JQuantsEndpoints.get_endpoint_by_path("/listed/info")
        assert endpoint is not None
        assert endpoint.path == "/listed/info"

    def test_get_endpoint_by_path_not_found(self) -> None:
        """Test handling non-existent endpoint path."""
        endpoint = JQuantsEndpoints.get_endpoint_by_path("/nonexistent")
        assert endpoint is None


# ==================== JQuantsClient Tests ====================


class TestJQuantsClient:
    """Test JQuantsClient class."""

    def test_client_initialization(self, client: JQuantsClient) -> None:
        """Test client initialization."""
        assert client.base_url == "https://api.jquants.com/v1"
        assert client.rate_limit_delay == 0.1
        assert client.authenticator is not None

    def test_rate_limiting(self, client: JQuantsClient) -> None:
        """Test that rate limiting is enforced."""
        client._last_request_time = time.time()
        start_time = time.time()
        client._enforce_rate_limit()
        elapsed = time.time() - start_time
        # Should have waited approximately rate_limit_delay seconds
        assert elapsed >= client.rate_limit_delay * 0.9  # Allow some tolerance

    @responses.activate
    def test_make_request_success(self, client: JQuantsClient, mock_id_token: str) -> None:
        """Test successful API request."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/listed/info",
            json={"info": [{"code": "27800", "name": "Test Company"}]},
            status=200,
        )

        result = client._make_request("/listed/info", params={"code": "27800"})
        assert "info" in result
        assert len(result["info"]) == 1

    @responses.activate
    def test_make_request_401_invalidates_token(
        self, client: JQuantsClient, mock_id_token: str
    ) -> None:
        """Test that 401 error invalidates token."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/listed/info",
            json={"error": "Unauthorized"},
            status=401,
        )

        with pytest.raises(AuthenticationError):
            client._make_request("/listed/info")

        # Token should be invalidated
        assert client.authenticator._id_token is None

    @responses.activate
    def test_make_request_404_raises_not_found(
        self, client: JQuantsClient, mock_id_token: str
    ) -> None:
        """Test that 404 raises NotFoundError."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/nonexistent",
            json={"error": "Not found"},
            status=404,
        )

        with pytest.raises(NotFoundError):
            client._make_request("/nonexistent")

    @responses.activate
    def test_make_request_429_raises_rate_limit(
        self, client: JQuantsClient, mock_id_token: str
    ) -> None:
        """Test that 429 raises RateLimitError."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/listed/info",
            json={"error": "Rate limit exceeded"},
            status=429,
        )

        with pytest.raises(RateLimitError):
            client._make_request("/listed/info")

    @responses.activate
    def test_make_request_500_raises_api_error(
        self, client: JQuantsClient, mock_id_token: str
    ) -> None:
        """Test that 500 raises APIError."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/listed/info",
            json={"error": "Internal server error"},
            status=500,
        )

        with pytest.raises(APIError, match="Server error"):
            client._make_request("/listed/info")

    def test_to_dataframe_with_data(self, client: JQuantsClient) -> None:
        """Test converting API response to DataFrame."""
        response = {
            "data": [
                {"code": "27800", "name": "Company A"},
                {"code": "27810", "name": "Company B"},
            ]
        }
        df = client._to_dataframe(response, "data")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "code" in df.columns

    def test_to_dataframe_empty(self, client: JQuantsClient) -> None:
        """Test converting empty response to DataFrame."""
        response = {"data": []}
        df = client._to_dataframe(response, "data")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_to_dataframe_missing_key(self, client: JQuantsClient) -> None:
        """Test handling missing key in response."""
        response = {"other_key": []}
        df = client._to_dataframe(response, "data")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    @responses.activate
    def test_get_listed_info(self, client: JQuantsClient, mock_id_token: str) -> None:
        """Test getting listed company information."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/listed/info",
            json={"info": [{"code": "27800", "name": "Test Company"}]},
            status=200,
        )

        df = client.get_listed_info(code="27800")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @responses.activate
    def test_get_daily_quotes(self, client: JQuantsClient, mock_id_token: str) -> None:
        """Test getting daily quotes."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/prices/daily_quotes",
            json={
                "daily_quotes": [
                    {
                        "code": "27800",
                        "date": "2024-01-15",
                        "open": 1000,
                        "high": 1100,
                        "low": 950,
                        "close": 1050,
                    }
                ]
            },
            status=200,
        )

        df = client.get_daily_quotes(code="27800", date="20240115")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
        assert "close" in df.columns

    @responses.activate
    def test_get_financial_statements(
        self, client: JQuantsClient, mock_id_token: str
    ) -> None:
        """Test getting financial statements."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/fins/statements",
            json={"statements": [{"code": "27800", "revenue": 1000000}]},
            status=200,
        )

        df = client.get_financial_statements(code="27800")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @responses.activate
    def test_get_indices(self, client: JQuantsClient, mock_id_token: str) -> None:
        """Test getting index data."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/indices",
            json={"indices": [{"code": "0000", "value": 30000}]},
            status=200,
        )

        df = client.get_indices(code="0000", date="20240115")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @responses.activate
    def test_get_trades_by_investor_type(
        self, client: JQuantsClient, mock_id_token: str
    ) -> None:
        """Test getting trading by investor type."""
        client.authenticator._id_token = TokenInfo(
            token=mock_id_token, expires_at=time.time() + 3600
        )

        responses.add(
            responses.GET,
            f"{client.base_url}/markets/trades_spec",
            json={"trades_spec": [{"section": "TSE1", "foreign_buy": 1000000}]},
            status=200,
        )

        df = client.get_trades_by_investor_type(section="TSE1")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    def test_get_refresh_token(self, client: JQuantsClient, mock_refresh_token: str) -> None:
        """Test getting refresh token from client."""
        client.authenticator._refresh_token = mock_refresh_token
        token = client.get_refresh_token()
        assert token == mock_refresh_token

    def test_clear_cache(self, client: JQuantsClient, mock_refresh_token: str) -> None:
        """Test clearing token cache."""
        client.authenticator._refresh_token = mock_refresh_token
        client.clear_cache()
        assert client.authenticator._refresh_token is None
        assert client.authenticator._id_token is None


# ==================== Integration-like Tests ====================


class TestIntegration:
    """Integration-like tests for the complete flow."""

    @responses.activate
    def test_complete_authentication_flow(
        self, mock_email: str, mock_password: str, base_url: str
    ) -> None:
        """Test complete authentication flow from email/password to API call."""
        # Mock refresh token acquisition
        responses.add(
            responses.POST,
            f"{base_url}/token/auth_user",
            json={"refreshToken": "refresh_123"},
            status=200,
        )

        # Mock ID token acquisition
        responses.add(
            responses.POST,
            f"{base_url}/token/auth_refresh",
            json={"idToken": "id_456"},
            status=200,
        )

        # Mock API call
        responses.add(
            responses.GET,
            f"{base_url}/listed/info",
            json={"info": [{"code": "27800"}]},
            status=200,
        )

        client = JQuantsClient(email=mock_email, password=mock_password, base_url=base_url)
        df = client.get_listed_info(code="27800")

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1

    @responses.activate
    def test_retry_on_failure(
        self, mock_email: str, mock_password: str, base_url: str
    ) -> None:
        """Test that requests are retried on failure."""
        # Mock authentication
        responses.add(
            responses.POST,
            f"{base_url}/token/auth_refresh",
            json={"idToken": "id_456"},
            status=200,
        )

        # First request fails, second succeeds
        responses.add(
            responses.GET,
            f"{base_url}/listed/info",
            json={"error": "Temporary error"},
            status=500,
        )
        responses.add(
            responses.GET,
            f"{base_url}/listed/info",
            json={"info": [{"code": "27800"}]},
            status=200,
        )

        client = JQuantsClient(
            email=mock_email,
            password=mock_password,
            base_url=base_url,
            refresh_token="refresh_123",
        )

        df = client.get_listed_info(code="27800")
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 1
