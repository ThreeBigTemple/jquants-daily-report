# J-Quants API Client

Comprehensive Python client for the J-Quants API Standard plan with authentication, rate limiting, and automatic retry.

## Features

- **Complete Authentication Flow**: Automatic handling of refresh tokens and ID tokens
- **Rate Limiting**: Configurable rate limiting (default: 1 request/second)
- **Automatic Retry**: Exponential backoff retry logic for failed requests
- **Type Safety**: Full type hints for all methods
- **DataFrame Output**: Direct conversion to pandas DataFrame
- **Error Handling**: Custom exceptions for different error types

## Quick Start

```python
from jquants_report.api import JQuantsClient

# Initialize client
client = JQuantsClient(
    email="your-email@example.com",
    password="your-password",
    refresh_token="optional-refresh-token"  # Save this to avoid repeated auth
)

# Get listed company information
companies = client.get_listed_info(code="27800")

# Get daily stock quotes
quotes = client.get_daily_quotes(
    code="27800",
    from_date="2024-01-01",
    to_date="2024-01-31"
)

# Get financial statements
financials = client.get_financial_statements(code="27800")

# Get index data
topix = client.get_indices(code="0000", date="2024-01-15")
```

## Authentication

The client handles authentication automatically using a two-step process:

1. **Refresh Token**: Obtained using email/password (valid for 24 hours)
2. **ID Token**: Obtained using refresh token (valid for 24 hours)

```python
# Get and save refresh token to avoid repeated email/password auth
refresh_token = client.get_refresh_token()
print(f"Save this token: {refresh_token}")

# Use refresh token in future sessions
client = JQuantsClient(
    email="your-email@example.com",
    password="your-password",
    refresh_token=refresh_token
)
```

## Available Endpoints

### Listed Information
- `get_listed_info(code, date)` - Company information
- `get_listed_sections(code)` - Section information

### Price Data
- `get_daily_quotes(code, date, from_date, to_date)` - Daily OHLCV data
- `get_prices_am(code, date, from_date, to_date)` - Morning session prices

### Financial Data
- `get_financial_statements(code, date)` - Financial statements
- `get_financial_announcement(code, date)` - Announcement schedules
- `get_dividend_info(code, date)` - Dividend information

### Index Data
- `get_indices(code, date, from_date, to_date)` - Index data
- `get_topix_composition(code, date)` - TOPIX composition and weights

### Market Data
- `get_trades_by_investor_type(section, date, from_date, to_date)` - Trading by investor type
- `get_short_selling(code, sector33code, date)` - Short selling data
- `get_margin_trading(code, date)` - Margin trading data
- `get_market_breakdown(date)` - Market breakdown
- `get_weekly_margin_trading(code, date)` - Weekly margin trading

### Derivatives
- `get_index_option(date)` - Index option data
- `get_index_futures(date)` - Index futures data

### Disclosure
- `get_tdnet_disclosure(code, date)` - TDnet disclosure information

## Error Handling

The client provides specific exceptions for different error types:

```python
from jquants_report.api import (
    JQuantsClient,
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    APIError
)

try:
    quotes = client.get_daily_quotes(code="27800")
except AuthenticationError:
    print("Authentication failed - check credentials")
except RateLimitError:
    print("Rate limit exceeded - slow down requests")
except NotFoundError:
    print("Resource not found")
except APIError as e:
    print(f"API error: {e}")
```

## Rate Limiting

The client enforces rate limiting to comply with API restrictions:

```python
# Default: 1 request per second
client = JQuantsClient(
    email="your-email@example.com",
    password="your-password",
    rate_limit_delay=1.0  # seconds between requests
)

# Custom rate limit (e.g., 2 seconds between requests)
client = JQuantsClient(
    email="your-email@example.com",
    password="your-password",
    rate_limit_delay=2.0
)
```

## Automatic Retry

Failed requests are automatically retried with exponential backoff:

- **Max attempts**: 3
- **Wait time**: Exponential (2s, 4s, 8s, up to 10s max)
- **Retry conditions**: Network errors, server errors (5xx)

```python
# This will automatically retry up to 3 times
quotes = client.get_daily_quotes(code="27800")
```

## Advanced Usage

### Custom Base URL

```python
client = JQuantsClient(
    email="your-email@example.com",
    password="your-password",
    base_url="https://custom-api.example.com/v1"
)
```

### Token Management

```python
# Invalidate cached ID token (forces refresh on next request)
client.authenticator.invalidate_tokens()

# Clear all tokens including refresh token
client.clear_cache()
```

### Direct Authenticator Usage

```python
from jquants_report.api import JQuantsAuthenticator

auth = JQuantsAuthenticator(
    base_url="https://api.jquants.com/v1",
    email="your-email@example.com",
    password="your-password"
)

# Get authentication headers for manual requests
headers = auth.get_auth_headers()
print(headers)  # {'Authorization': 'Bearer <id_token>'}
```

## Date Formats

The API accepts dates in two formats:

- `YYYYMMDD`: `"20240115"`
- `YYYY-MM-DD`: `"2024-01-15"`

```python
# Both formats work
quotes1 = client.get_daily_quotes(date="20240115")
quotes2 = client.get_daily_quotes(date="2024-01-15")
```

## Response Format

All data methods return pandas DataFrames:

```python
quotes = client.get_daily_quotes(code="27800", date="2024-01-15")

print(type(quotes))  # <class 'pandas.core.frame.DataFrame'>
print(quotes.columns)
print(quotes.head())

# Empty DataFrame if no data
if quotes.empty:
    print("No data available")
```

## Testing

The module includes comprehensive unit tests:

```bash
# Run all tests
uv run pytest tests/test_api.py -v

# Run with coverage
uv run pytest tests/test_api.py --cov=jquants_report.api

# Run specific test class
uv run pytest tests/test_api.py::TestJQuantsClient -v
```

## Type Checking

All code includes type hints and can be checked with mypy:

```bash
uv run mypy src/jquants_report/api/
```

## Examples

See `examples/api_usage_example.py` for more usage examples:

```bash
uv run python examples/api_usage_example.py
```

## API Reference

For detailed API documentation, refer to:
- [J-Quants API Documentation](https://jpx.gitbook.io/j-quants-ja)
- [J-Quants API Reference](https://jpx.gitbook.io/j-quants-ja/api-reference)

## License

MIT License - See project LICENSE file for details.
