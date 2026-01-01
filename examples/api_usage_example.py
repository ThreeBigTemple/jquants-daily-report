"""Example usage of J-Quants API client.

This example demonstrates how to use the J-Quants API client for common tasks.
"""

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

from jquants_report.api import JQuantsClient

# Load environment variables
load_dotenv()


def main() -> None:
    """Main function demonstrating API client usage."""
    # Initialize the client
    client = JQuantsClient(
        email=os.getenv("JQUANTS_EMAIL", ""),
        password=os.getenv("JQUANTS_PASSWORD", ""),
        refresh_token=os.getenv("JQUANTS_REFRESH_TOKEN"),  # Optional
    )

    print("=== J-Quants API Client Usage Examples ===\n")

    # Example 1: Get listed company information
    print("1. Getting listed company information for code 27800...")
    listed_info = client.get_listed_info(code="27800")
    print(f"   Retrieved {len(listed_info)} records")
    if not listed_info.empty:
        print(f"   Columns: {', '.join(listed_info.columns)}\n")

    # Example 2: Get daily quotes for a specific date
    print("2. Getting daily quotes for 2024-01-15...")
    daily_quotes = client.get_daily_quotes(date="2024-01-15")
    print(f"   Retrieved {len(daily_quotes)} records")
    if not daily_quotes.empty:
        print(f"   Sample data:\n{daily_quotes.head()}\n")

    # Example 3: Get daily quotes for a date range
    print("3. Getting daily quotes for a date range...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    quotes_range = client.get_daily_quotes(
        code="27800",
        from_date=start_date.strftime("%Y-%m-%d"),
        to_date=end_date.strftime("%Y-%m-%d"),
    )
    print(f"   Retrieved {len(quotes_range)} records for the past week\n")

    # Example 4: Get financial statements
    print("4. Getting financial statements...")
    statements = client.get_financial_statements(code="27800")
    print(f"   Retrieved {len(statements)} records")
    if not statements.empty:
        print(f"   Columns: {', '.join(statements.columns)}\n")

    # Example 5: Get index data (TOPIX)
    print("5. Getting TOPIX index data...")
    indices = client.get_indices(code="0000", date="2024-01-15")
    print(f"   Retrieved {len(indices)} records")
    if not indices.empty:
        print(f"   Sample data:\n{indices.head()}\n")

    # Example 6: Get trading by investor type
    print("6. Getting trading by investor type...")
    trades = client.get_trades_by_investor_type(date="2024-01-15")
    print(f"   Retrieved {len(trades)} records")
    if not trades.empty:
        print(f"   Columns: {', '.join(trades.columns)}\n")

    # Example 7: Get short selling data
    print("7. Getting short selling data...")
    short_selling = client.get_short_selling(date="2024-01-15")
    print(f"   Retrieved {len(short_selling)} records\n")

    # Example 8: Get margin trading data
    print("8. Getting margin trading data...")
    margin = client.get_margin_trading(code="27800")
    print(f"   Retrieved {len(margin)} records\n")

    # Save refresh token for future use
    print("9. Saving refresh token for future use...")
    refresh_token = client.get_refresh_token()
    print(f"   Refresh token: {refresh_token[:20]}...")
    print("   (Save this to JQUANTS_REFRESH_TOKEN in your .env file)\n")

    print("=== Examples completed successfully ===")


if __name__ == "__main__":
    main()
