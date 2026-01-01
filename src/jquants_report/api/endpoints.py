"""API endpoint definitions for J-Quants API.

This module defines all available endpoints for the J-Quants API Standard plan.
Each endpoint is represented as a constant with its path and common parameters.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Endpoint:
    """Represents an API endpoint with its path and description.

    Attributes:
        path: The API endpoint path (e.g., "/listed/info").
        description: A brief description of what the endpoint returns.
        params: Common parameters for the endpoint.
    """

    path: str
    description: str
    params: dict[str, str]


class JQuantsEndpoints:
    """Container for all J-Quants API endpoint definitions.

    This class provides access to all available endpoints in the J-Quants API.
    Endpoints are organized by category (listed info, prices, financials, etc.).
    """

    # Listed Information Endpoints
    LISTED_INFO = Endpoint(
        path="/listed/info",
        description="Get information about listed companies",
        params={
            "code": "Stock code (e.g., '27800' or '2780')",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    LISTED_SECTIONS = Endpoint(
        path="/listed/sections",
        description="Get section information for listed companies",
        params={
            "code": "Stock code",
        },
    )

    # Price Data Endpoints
    PRICES_DAILY_QUOTES = Endpoint(
        path="/prices/daily_quotes",
        description="Get daily stock quotes (OHLCV data)",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
            "from": "Start date",
            "to": "End date",
        },
    )

    PRICES_AM = Endpoint(
        path="/prices/prices_am",
        description="Get morning session prices",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
            "from": "Start date",
            "to": "End date",
        },
    )

    # Financial Data Endpoints
    FINS_STATEMENTS = Endpoint(
        path="/fins/statements",
        description="Get financial statements data",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    FINS_ANNOUNCEMENT = Endpoint(
        path="/fins/announcement",
        description="Get financial announcement schedules",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    FINS_DIVIDEND = Endpoint(
        path="/fins/dividend",
        description="Get dividend information",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    # Index Data Endpoints
    INDICES = Endpoint(
        path="/indices",
        description="Get index data",
        params={
            "code": "Index code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
            "from": "Start date",
            "to": "End date",
        },
    )

    INDICES_TOPIX = Endpoint(
        path="/indices/topix",
        description="Get TOPIX index composition and weights",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    # Market Data Endpoints
    MARKETS_TRADES_SPEC = Endpoint(
        path="/markets/trades_spec",
        description="Get trading by investor type (institutional, foreign, etc.)",
        params={
            "section": "Market section code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
            "from": "Start date",
            "to": "End date",
        },
    )

    MARKETS_SHORT_SELLING = Endpoint(
        path="/markets/short_selling",
        description="Get short selling data",
        params={
            "code": "Stock code",
            "sector33code": "Sector code (33 sectors)",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    MARKETS_MARGIN_INTEREST = Endpoint(
        path="/markets/margin_interest",
        description="Get margin trading data",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    MARKETS_BREAKDOWN = Endpoint(
        path="/markets/breakdown",
        description="Get market breakdown by value/volume",
        params={
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    MARKETS_WEEKLY_MARGIN_INTEREST = Endpoint(
        path="/markets/weekly_margin_interest",
        description="Get weekly margin trading data",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    # Options Data Endpoints
    OPTION_INDEX_OPTION = Endpoint(
        path="/option/index_option",
        description="Get index option data",
        params={
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    # Futures Data Endpoints
    FUTURES_INDEX_FUTURES = Endpoint(
        path="/futures/index_futures",
        description="Get index futures data",
        params={
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    # News and Disclosure Endpoints
    DISCLOSURE_TDNET = Endpoint(
        path="/disclosure/tdnet",
        description="Get TDnet disclosure information",
        params={
            "code": "Stock code",
            "date": "Date in YYYYMMDD or YYYY-MM-DD format",
        },
    )

    @classmethod
    def get_all_endpoints(cls) -> dict[str, Endpoint]:
        """Get all available endpoints as a dictionary.

        Returns:
            Dictionary mapping endpoint names to Endpoint objects.
        """
        return {
            name: getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), Endpoint)
        }

    @classmethod
    def get_endpoint_by_path(cls, path: str) -> Endpoint | None:
        """Find an endpoint by its path.

        Args:
            path: The endpoint path to search for.

        Returns:
            The Endpoint object if found, None otherwise.
        """
        for endpoint in cls.get_all_endpoints().values():
            if endpoint.path == path:
                return endpoint
        return None


def build_query_params(**kwargs: Any) -> dict[str, str]:
    """Build query parameters for API requests, filtering out None values.

    Args:
        **kwargs: Arbitrary keyword arguments representing query parameters.

    Returns:
        Dictionary of query parameters with None values removed.

    Example:
        >>> build_query_params(code="27800", date="20240115", limit=None)
        {'code': '27800', 'date': '20240115'}
    """
    return {k: str(v) for k, v in kwargs.items() if v is not None}
