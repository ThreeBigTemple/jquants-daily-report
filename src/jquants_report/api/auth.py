"""Authentication module for J-Quants API.

This module handles authentication for the J-Quants API, including:
- Refresh token acquisition
- ID token acquisition and refresh
- Token expiration management
"""

import logging
import time
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class TokenExpiredError(Exception):
    """Raised when a token has expired."""

    pass


@dataclass
class TokenInfo:
    """Container for authentication token information.

    Attributes:
        token: The authentication token string.
        expires_at: Unix timestamp when the token expires.
    """

    token: str
    expires_at: float

    def is_expired(self, buffer_seconds: int = 300) -> bool:
        """Check if token is expired or close to expiring.

        Args:
            buffer_seconds: Number of seconds before expiration to consider token expired.
                           Default is 300 (5 minutes) to prevent edge cases.

        Returns:
            True if token is expired or will expire within buffer_seconds.
        """
        return time.time() >= (self.expires_at - buffer_seconds)


class JQuantsAuthenticator:
    """Handles authentication flow for J-Quants API.

    This class manages the complete authentication flow:
    1. Obtain refresh token using email/password
    2. Obtain ID token using refresh token
    3. Automatically refresh ID token when expired

    Attributes:
        base_url: Base URL for J-Quants API.
        email: User email for authentication.
        password: User password for authentication.
        refresh_token: Refresh token (24-hour validity).
        id_token: ID token info (24-hour validity).
    """

    TOKEN_AUTH_USER_ENDPOINT = "/token/auth_user"
    TOKEN_AUTH_REFRESH_ENDPOINT = "/token/auth_refresh"

    def __init__(
        self,
        base_url: str,
        email: str,
        password: str,
        refresh_token: str | None = None,
    ) -> None:
        """Initialize the authenticator.

        Args:
            base_url: Base URL for J-Quants API.
            email: User email for authentication.
            password: User password for authentication.
            refresh_token: Optional pre-existing refresh token.
        """
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self._refresh_token = refresh_token
        self._id_token: TokenInfo | None = None

    def get_refresh_token(self) -> str:
        """Get a valid refresh token.

        If a refresh token exists and is valid, returns it.
        Otherwise, obtains a new refresh token using email/password.

        Returns:
            A valid refresh token string.

        Raises:
            AuthenticationError: If authentication fails.
        """
        if self._refresh_token:
            logger.debug("Using existing refresh token")
            return self._refresh_token

        logger.info("Obtaining new refresh token")
        url = f"{self.base_url}{self.TOKEN_AUTH_USER_ENDPOINT}"

        try:
            response = requests.post(
                url,
                json={"mailaddress": self.email, "password": self.password},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to obtain refresh token: {e}") from e

        data = response.json()
        if "refreshToken" not in data:
            raise AuthenticationError("Refresh token not found in response")

        self._refresh_token = data["refreshToken"]
        logger.info("Successfully obtained refresh token")

        return self._refresh_token

    def get_id_token(self, force_refresh: bool = False) -> str:
        """Get a valid ID token.

        If a valid ID token exists and is not expired, returns it.
        Otherwise, obtains a new ID token using the refresh token.

        Args:
            force_refresh: If True, forces refresh even if current token is valid.

        Returns:
            A valid ID token string.

        Raises:
            AuthenticationError: If authentication fails.
        """
        if not force_refresh and self._id_token and not self._id_token.is_expired():
            logger.debug("Using existing ID token")
            return self._id_token.token

        logger.info("Obtaining new ID token")
        refresh_token = self.get_refresh_token()
        url = f"{self.base_url}{self.TOKEN_AUTH_REFRESH_ENDPOINT}"

        try:
            response = requests.post(
                url,
                params={"refreshtoken": refresh_token},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            raise AuthenticationError(f"Failed to obtain ID token: {e}") from e

        data = response.json()
        if "idToken" not in data:
            raise AuthenticationError("ID token not found in response")

        # ID tokens are valid for 24 hours
        expires_at = time.time() + (24 * 60 * 60)
        self._id_token = TokenInfo(token=data["idToken"], expires_at=expires_at)

        logger.info("Successfully obtained ID token (valid for 24 hours)")
        return self._id_token.token

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests.

        Returns:
            Dictionary containing Authorization header with valid ID token.

        Raises:
            AuthenticationError: If unable to obtain valid token.
        """
        id_token = self.get_id_token()
        return {"Authorization": f"Bearer {id_token}"}

    def invalidate_tokens(self) -> None:
        """Invalidate cached tokens to force refresh on next request."""
        logger.info("Invalidating cached tokens")
        self._id_token = None

    def clear_all_tokens(self) -> None:
        """Clear all tokens including refresh token."""
        logger.info("Clearing all tokens")
        self._refresh_token = None
        self._id_token = None
