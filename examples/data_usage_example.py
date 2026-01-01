"""Example usage of data processing modules.

This demonstrates how to use the DataFetcher, DataProcessor, and CacheManager
together to fetch and process J-Quants data.
"""

from datetime import date, timedelta
from pathlib import Path

from jquants_report.data.cache import CacheManager
from jquants_report.data.fetcher import DataFetcher
from jquants_report.data.processor import DataProcessor


def example_basic_usage():
    """Basic example of fetching and processing data."""
    print("=" * 80)
    print("Basic Usage Example")
    print("=" * 80)

    # NOTE: This example requires a real JQuantsClient instance
    # For demonstration, we'll show the structure without actual API calls

    # Initialize components
    cache_dir = Path("./data/cache")
    cache_manager = CacheManager(cache_dir, default_ttl_hours=24)
    processor = DataProcessor()

    # In a real application, you would initialize the API client:
    # from jquants_report.api.client import JQuantsClient
    # api_client = JQuantsClient(config)
    # fetcher = DataFetcher(api_client, cache_manager)

    print("\n1. Cache Manager initialized")
    print(f"   Cache directory: {cache_manager.cache_dir}")
    print(f"   Default TTL: {cache_manager.default_ttl_hours} hours")

    print("\n2. Data Processor initialized")
    print("   Ready to process various data types")

    # Example workflow (requires real API client):
    # target_date = date.today() - timedelta(days=1)
    #
    # # Fetch data
    # print(f"\n3. Fetching data for {target_date}")
    # daily_quotes = fetcher.fetch_daily_quotes(target_date)
    # listed_info = fetcher.fetch_listed_info()
    #
    # # Process data
    # print("\n4. Processing data")
    # processed_quotes = processor.process_daily_quotes(daily_quotes)
    # processed_info = processor.process_listed_info(listed_info)
    #
    # # Merge with master data
    # print("\n5. Merging with master data")
    # enriched_data = processor.merge_with_master(
    #     processed_quotes,
    #     processed_info,
    #     on="code"
    # )
    #
    # print(f"\n6. Final dataset: {len(enriched_data)} records")
    # print(f"   Columns: {list(enriched_data.columns)}")


def example_cache_operations():
    """Example of cache operations."""
    print("\n" + "=" * 80)
    print("Cache Operations Example")
    print("=" * 80)

    import pandas as pd

    cache_dir = Path("./data/cache_example")
    cache_manager = CacheManager(cache_dir, default_ttl_hours=1)

    # Create sample data
    sample_data = pd.DataFrame({
        "code": ["1301", "1302", "1303"],
        "price": [100, 200, 300],
        "volume": [1000, 2000, 3000],
    })

    # Set cache
    print("\n1. Storing data in cache")
    cache_manager.set("sample_data", sample_data, ttl_hours=1)
    print("   Cache stored successfully")

    # Get cache
    print("\n2. Retrieving data from cache")
    cached_data = cache_manager.get("sample_data")
    if cached_data is not None:
        print(f"   Retrieved {len(cached_data)} records")
        print(f"   Columns: {list(cached_data.columns)}")

    # Check cache size
    print("\n3. Cache information")
    cache_size = cache_manager.get_cache_size()
    print(f"   Total cache size: {cache_size:,} bytes ({cache_size / 1024:.2f} KB)")

    # Cleanup
    print("\n4. Cleanup expired entries")
    removed = cache_manager.cleanup_expired()
    print(f"   Removed {removed} expired entries")


def example_data_processing():
    """Example of data processing operations."""
    print("\n" + "=" * 80)
    print("Data Processing Example")
    print("=" * 80)

    import pandas as pd

    processor = DataProcessor()

    # Sample daily quotes
    raw_quotes = pd.DataFrame({
        "Code": ["1301", "1302", "1301"],
        "Date": ["2024-01-15", "2024-01-15", "2024-01-16"],
        "Open": ["100", "200", "102"],
        "Close": ["105", "205", "108"],
        "Volume": ["1000000", "500000", "1200000"],
    })

    print("\n1. Processing daily quotes")
    print(f"   Input: {len(raw_quotes)} records")
    processed = processor.process_daily_quotes(raw_quotes)
    print(f"   Output: {len(processed)} records")
    print(f"   Columns: {list(processed.columns)}")

    # Calculate statistics
    print("\n2. Calculating statistics")
    stats = processor.calculate_statistics(processed, value_column="close")
    print("\n   Price statistics:")
    for col in ["mean", "std", "min", "max"]:
        if col in stats.columns:
            print(f"   {col:8s}: {stats[col].iloc[0]:.2f}")

    # Filter by date
    print("\n3. Filtering by date")
    from datetime import datetime
    filtered = processor.filter_by_date_range(
        processed,
        start_date=datetime(2024, 1, 16),
        date_column="date"
    )
    print(f"   Filtered: {len(filtered)} records (date >= 2024-01-16)")

    # Filter by codes
    print("\n4. Filtering by stock codes")
    code_filtered = processor.filter_by_codes(
        processed,
        codes=["1301"],
        code_column="code"
    )
    print(f"   Filtered: {len(code_filtered)} records (code = 1301)")


def example_advanced_workflow():
    """Advanced workflow example."""
    print("\n" + "=" * 80)
    print("Advanced Workflow Example")
    print("=" * 80)

    import pandas as pd

    processor = DataProcessor()

    # Sample data
    quotes = pd.DataFrame({
        "Code": ["1301", "1302", "1303"],
        "Date": ["2024-01-15"] * 3,
        "Open": ["100", "200", "150"],
        "Close": ["105", "195", "155"],
        "Volume": ["1000000", "500000", "750000"],
    })

    master = pd.DataFrame({
        "Code": ["1301", "1302", "1303"],
        "CompanyName": ["Company A", "Company B", "Company C"],
        "Sector17CodeName": ["Electronics", "Finance", "Retail"],
    })

    print("\n1. Processing raw data")
    processed_quotes = processor.process_daily_quotes(quotes)
    processed_master = processor.process_listed_info(master)

    print("\n2. Merging with master data")
    merged = processor.merge_with_master(
        processed_quotes,
        processed_master,
        on="code"
    )
    print(f"   Merged dataset: {len(merged)} records")
    print(f"   Columns: {list(merged.columns)}")

    print("\n3. Grouped statistics by sector")
    if "sector_17_name" in merged.columns:
        sector_stats = processor.calculate_statistics(
            merged,
            value_column="close",
            group_by="sector_17_name"
        )
        print("\n   Sector statistics:")
        print(sector_stats.to_string(index=False))

    print("\n4. Top performers (by price change %)")
    if "price_change_pct" in merged.columns:
        top_performers = merged.nlargest(3, "price_change_pct")
        print("\n   Top 3 stocks:")
        for _, row in top_performers.iterrows():
            print(f"   {row['code']:6s} ({row.get('company_name', 'N/A'):20s}): "
                  f"{row['price_change_pct']:+.2f}%")


def main():
    """Run all examples."""
    print("\nJ-Quants Data Processing Module Examples")
    print("=" * 80)

    try:
        example_basic_usage()
        example_cache_operations()
        example_data_processing()
        example_advanced_workflow()

        print("\n" + "=" * 80)
        print("All examples completed successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
