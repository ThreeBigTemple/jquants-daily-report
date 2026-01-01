"""Main entry point for J-Quants Daily Report System."""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

from jquants_report.config import load_config


def setup_logging(log_level: str) -> None:
    """Set up logging configuration.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Generate daily stock market report using J-Quants API"
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Target date for report (YYYY-MM-DD format). Defaults to today.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without API calls, use cached data only.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for reports. Overrides config.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level. Overrides config.",
    )
    parser.add_argument(
        "--weekly",
        action="store_true",
        help="Generate weekly report instead of daily report.",
    )
    parser.add_argument(
        "--week-end",
        type=str,
        default=None,
        help="Week end date for weekly report (YYYY-MM-DD). Defaults to most recent Friday.",
    )
    return parser.parse_args()


def parse_date(date_str: str | None) -> date:
    """Parse date string to date object.

    Args:
        date_str: Date string in YYYY-MM-DD format or None.

    Returns:
        Parsed date or today's date if None.

    Raises:
        ValueError: If date string is invalid.
    """
    if date_str is None:
        return date.today()
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError as e:
        raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD.") from e


def generate_report(target_date: date, dry_run: bool, output_dir: Path) -> Path:
    """Generate daily market report.

    Args:
        target_date: The target date for the report.
        dry_run: If True, use cached data only.
        output_dir: Directory to save the report.

    Returns:
        Path to the generated report file.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Generating report for {target_date}")

    # Import modules here to avoid circular imports
    from jquants_report.analysis.market import MarketAnalyzer
    from jquants_report.analysis.sector import SectorAnalyzer
    from jquants_report.analysis.stocks import StockAnalyzer
    from jquants_report.analysis.supply_demand import SupplyDemandAnalyzer
    from jquants_report.analysis.technical import TechnicalAnalyzer
    from jquants_report.api import JQuantsClient
    from jquants_report.data import CacheManager, DataFetcher
    from jquants_report.report import (
        IndexData,
        MarketSummary,
        ReportGenerator,
        SectorAnalysis,
        SectorData,
        StockData,
        StockHighlights,
        SupplyDemandSummary,
        TechnicalIndicator,
        TechnicalSummary,
    )

    config = load_config()

    # Initialize components
    client = JQuantsClient(
        email=config.jquants.email,
        password=config.jquants.password,
        refresh_token=config.jquants.refresh_token,
        base_url=config.jquants.base_url,
    )
    cache = CacheManager(config.app.cache_dir)
    fetcher = DataFetcher(client, cache)

    # Fetch data
    date_str = target_date.strftime("%Y-%m-%d")

    if dry_run:
        logger.info("Dry run mode: using cached data only")
        prices_df = cache.get(f"daily_quotes_{date_str}") or fetcher.fetch_daily_quotes(
            target_date
        )
        indices_df = (
            cache.get(f"indices_{date_str}") or fetcher.fetch_indices(target_date)
        )
        listed_info_df = cache.get("listed_info") or fetcher.fetch_listed_info()
    else:
        logger.info("Fetching market data...")
        prices_df = fetcher.fetch_daily_quotes(target_date)
        indices_df = fetcher.fetch_indices(target_date)
        listed_info_df = fetcher.fetch_listed_info()

    # Merge listed info with prices to get company names and sector info
    if not prices_df.empty and not listed_info_df.empty:
        logger.info("Enriching price data with company info...")
        # Merge on Code
        prices_df = prices_df.merge(
            listed_info_df[
                ["Code", "CompanyName", "Sector33Code", "Sector33CodeName"]
            ].drop_duplicates("Code"),
            on="Code",
            how="left",
        )

    # Fetch previous day's data to calculate change rates
    prev_date = target_date - timedelta(days=1)
    # Skip weekends
    while prev_date.weekday() >= 5:
        prev_date -= timedelta(days=1)

    prev_prices_df = cache.get(f"daily_quotes_{prev_date.strftime('%Y-%m-%d')}")
    if prev_prices_df is None and not dry_run:
        prev_prices_df = fetcher.fetch_daily_quotes(prev_date)

    # Calculate change rate if we have previous day's data
    if prev_prices_df is not None and not prev_prices_df.empty and not prices_df.empty:
        logger.info("Calculating change rates...")
        prev_close = prev_prices_df[["Code", "Close"]].rename(
            columns={"Close": "PrevClose"}
        )
        prices_df = prices_df.merge(prev_close, on="Code", how="left")
        prices_df["ChangeRate"] = (
            (prices_df["Close"] - prices_df["PrevClose"]) / prices_df["PrevClose"] * 100
        )

    # Fetch previous day's index data to calculate index changes
    prev_indices_df = cache.get(f"indices_{prev_date.strftime('%Y-%m-%d')}")
    if prev_indices_df is None and not dry_run:
        prev_indices_df = fetcher.fetch_indices(prev_date)

    # Calculate change rate for indices
    if (
        prev_indices_df is not None
        and not prev_indices_df.empty
        and not indices_df.empty
    ):
        logger.info("Calculating index change rates...")
        prev_idx_close = prev_indices_df[["Code", "Close"]].rename(
            columns={"Close": "PrevClose"}
        )
        indices_df = indices_df.merge(prev_idx_close, on="Code", how="left")
        indices_df["Change"] = indices_df["Close"] - indices_df["PrevClose"]
        indices_df["ChangeRate"] = (
            indices_df["Change"] / indices_df["PrevClose"] * 100
        )

    # Fetch historical data for technical analysis
    # Note: J-Quants API doesn't support date range query without code parameter
    # So we fetch past days one by one (limited to recent 30 days for performance)
    historical_df = None
    if not dry_run:
        logger.info("Fetching historical data for technical analysis...")
        all_historical: list = []
        # Fetch past 30 trading days (for 25-day MA calculation)
        for days_ago in range(1, 35):
            hist_date = target_date - timedelta(days=days_ago)
            # Skip weekends
            if hist_date.weekday() >= 5:
                continue
            hist_df = fetcher.fetch_daily_quotes(hist_date)
            if not hist_df.empty:
                all_historical.append(hist_df)
            # Stop if we have enough data
            if len(all_historical) >= 25:
                break
        if all_historical:
            import pandas as pd_  # Local import to avoid circular dependency
            historical_df = pd_.concat(all_historical, ignore_index=True)
            logger.info(f"Fetched {len(all_historical)} days of historical data")
    else:
        historical_df = cache.get("historical_prices")

    # Calculate ChangeRate for historical data (required for advance-decline ratio)
    if historical_df is not None and not historical_df.empty:
        historical_df = historical_df.sort_values(["Code", "Date"])
        historical_df["PrevClose"] = historical_df.groupby("Code")["Close"].shift(1)
        historical_df["ChangeRate"] = (
            (historical_df["Close"] - historical_df["PrevClose"])
            / historical_df["PrevClose"]
            * 100
        )
        logger.info("Calculated ChangeRate for historical data")

    # Fetch supply/demand data
    investor_df = None
    margin_df = None
    short_selling_df = None
    if not dry_run:
        logger.info("Fetching supply/demand data...")
        investor_df = fetcher.fetch_trades_spec(target_date)
        margin_df = fetcher.fetch_margin_interest(target_date)
        short_selling_df = fetcher.fetch_short_selling(target_date)
    else:
        investor_df = cache.get(f"trades_spec_{date_str}")
        margin_df = cache.get(f"margin_interest_{date_str}")
        short_selling_df = cache.get(f"short_selling_{date_str}")

    # Run analysis
    logger.info("Running analysis...")
    market_analyzer = MarketAnalyzer()
    sector_analyzer = SectorAnalyzer()
    stock_analyzer = StockAnalyzer()
    technical_analyzer = TechnicalAnalyzer()
    supply_demand_analyzer = SupplyDemandAnalyzer()

    # Market analysis
    market_overview = market_analyzer.analyze(date_str, prices_df, indices_df)

    # Sector analysis
    sector_performances = sector_analyzer.analyze_sectors(prices_df)

    # Stock analysis
    top_gainers = stock_analyzer.get_top_gainers(prices_df, top_n=10)
    top_losers = stock_analyzer.get_top_losers(prices_df, top_n=10)
    high_volume_stocks = stock_analyzer.get_high_volume_stocks(prices_df, top_n=10)

    # Technical analysis
    technical_indicators = technical_analyzer.analyze(date_str, prices_df, historical_df)

    # Supply/Demand analysis (using fetched data)
    supply_demand_result = supply_demand_analyzer.analyze(
        date=date_str,
        trading_df=investor_df,
        margin_df=margin_df,
    )

    # Convert analysis results to report format
    logger.info("Generating report...")

    # Build MarketSummary
    indices = []
    if market_overview.topix_close is not None:
        indices.append(
            IndexData(
                name="TOPIX",
                close=market_overview.topix_close,
                change=market_overview.topix_change or 0.0,
                change_pct=market_overview.topix_change_pct or 0.0,
            )
        )
    if market_overview.nikkei225_close is not None:
        indices.append(
            IndexData(
                name="日経225",
                close=market_overview.nikkei225_close,
                change=market_overview.nikkei225_change or 0.0,
                change_pct=market_overview.nikkei225_change_pct or 0.0,
            )
        )

    market_summary = MarketSummary(
        indices=indices,
        advancing=market_overview.advancing_issues,
        declining=market_overview.declining_issues,
        unchanged=market_overview.unchanged_issues,
        total_volume=market_overview.total_volume,
        total_turnover=market_overview.total_value,
    )

    # Build SectorAnalysis
    sector_data_list = [
        SectorData(
            name=sp.sector_name,
            change_pct=sp.average_change_pct,
            turnover=sp.total_value,
        )
        for sp in sorted(sector_performances, key=lambda x: x.average_change_pct, reverse=True)[:10]
    ]
    sector_analysis = SectorAnalysis(sectors=sector_data_list)

    # Build StockHighlights
    from jquants_report.analysis.stocks import StockInfo

    def convert_stock_info(stock_info_list: list[StockInfo]) -> list[StockData]:
        def normalize_code(code: str) -> str:
            """Normalize stock code to 4 digits (remove trailing 0 if 5 digits)."""
            if len(code) == 5 and code.endswith("0"):
                return code[:4]
            return code

        return [
            StockData(
                code=normalize_code(s.code),
                name=s.name,
                close=s.close,
                change=s.change,
                change_pct=s.change_pct,
                volume=int(s.volume),
                turnover=s.turnover_value,
            )
            for s in stock_info_list
        ]

    # Get top turnover stocks (separate from high volume)
    top_turnover_stocks = stock_analyzer.get_top_turnover_stocks(prices_df, top_n=10)

    stock_highlights = StockHighlights(
        top_gainers=convert_stock_info(top_gainers),
        top_losers=convert_stock_info(top_losers),
        top_volume=convert_stock_info(high_volume_stocks),
        top_turnover=convert_stock_info(top_turnover_stocks),
    )

    # Build TechnicalSummary
    moving_averages = []
    if technical_indicators.stocks_above_ma25_pct is not None:
        moving_averages.append(
            TechnicalIndicator(
                name="25日線上回り銘柄比率",
                value=technical_indicators.stocks_above_ma25_pct,
                signal="買い" if technical_indicators.stocks_above_ma25_pct > 50 else "売り",
            )
        )
    if technical_indicators.stocks_above_ma75_pct is not None:
        moving_averages.append(
            TechnicalIndicator(
                name="75日線上回り銘柄比率",
                value=technical_indicators.stocks_above_ma75_pct,
                signal="買い" if technical_indicators.stocks_above_ma75_pct > 50 else "売り",
            )
        )

    momentum_indicators = []
    if technical_indicators.advance_decline_ratio_25d is not None:
        momentum_indicators.append(
            TechnicalIndicator(
                name="騰落レシオ(25日)",
                value=technical_indicators.advance_decline_ratio_25d,
                signal="買われ過ぎ"
                if technical_indicators.advance_decline_ratio_25d > 120
                else "売られ過ぎ"
                if technical_indicators.advance_decline_ratio_25d < 80
                else "中立",
            )
        )

    technical_summary = TechnicalSummary(
        moving_averages=moving_averages,
        momentum_indicators=momentum_indicators,
    )

    # Build SupplyDemandSummary
    margin_buying = 0.0
    margin_selling = 0.0
    margin_ratio = 0.0
    if supply_demand_result.margin_trading is not None:
        margin_buying = supply_demand_result.margin_trading.margin_buy_balance
        margin_selling = supply_demand_result.margin_trading.margin_sell_balance
        margin_ratio = supply_demand_result.margin_trading.margin_ratio or 0.0

    # Calculate short selling ratio from fetched data
    short_selling_ratio = 0.0
    if short_selling_df is not None and not short_selling_df.empty:
        # Average short selling ratio across all stocks
        if "ShortSellingRatio" in short_selling_df.columns:
            short_selling_ratio = float(short_selling_df["ShortSellingRatio"].mean())
        elif "short_selling_ratio" in short_selling_df.columns:
            short_selling_ratio = float(short_selling_df["short_selling_ratio"].mean())

    supply_demand = SupplyDemandSummary(
        margin_buying_balance=margin_buying,
        margin_selling_balance=margin_selling,
        margin_ratio=margin_ratio,
        short_selling_ratio=short_selling_ratio,
    )

    # Generate report
    generator = ReportGenerator(output_dir)
    report_path = generator.generate(
        target_date=target_date,
        market_summary=market_summary,
        sector_analysis=sector_analysis,
        stock_highlights=stock_highlights,
        technical_summary=technical_summary,
        supply_demand=supply_demand,
    )

    logger.info(f"Report generated: {report_path}")
    return report_path


def get_latest_friday(reference_date: date | None = None) -> date:
    """Get the most recent Friday.

    Args:
        reference_date: Reference date. Defaults to today.

    Returns:
        Most recent Friday date.
    """
    if reference_date is None:
        reference_date = date.today()

    days_since_friday = (reference_date.weekday() - 4) % 7
    return reference_date - timedelta(days=days_since_friday)


def generate_weekly_report(week_end: date, dry_run: bool, output_dir: Path) -> Path:
    """Generate weekly market report.

    Args:
        week_end: The Friday (or last trading day) of the week.
        dry_run: If True, use cached data only.
        output_dir: Directory to save the report.

    Returns:
        Path to the generated report file.
    """
    import pandas as pd

    from jquants_report.analysis.weekly import (
        WeeklyEventsAnalyzer,
        WeeklyInvestorAnalyzer,
        WeeklyMarginAnalyzer,
        WeeklyMarketAnalyzer,
        WeeklySectorAnalyzer,
        WeeklyStockAnalyzer,
        WeeklyTechnicalAnalyzer,
        WeeklyTopicsAnalyzer,
        WeeklyTrendsAnalyzer,
    )
    from jquants_report.api import JQuantsClient
    from jquants_report.data import CacheManager, DataFetcher
    from jquants_report.data.weekly_aggregator import WeeklyDataAggregator
    from jquants_report.report.weekly_generator import WeeklyReportGenerator

    logger = logging.getLogger(__name__)
    logger.info(f"Generating weekly report for week ending {week_end}")

    config = load_config()

    # Initialize components
    client = JQuantsClient(
        email=config.jquants.email,
        password=config.jquants.password,
        refresh_token=config.jquants.refresh_token,
        base_url=config.jquants.base_url,
    )
    cache = CacheManager(config.app.cache_dir)
    fetcher = DataFetcher(client, cache) if not dry_run else None
    aggregator = WeeklyDataAggregator(cache, fetcher)

    # Calculate week dates
    trading_days = aggregator.get_week_trading_days(week_end)
    week_start = trading_days[0] if trading_days else week_end - timedelta(days=4)
    prev_week_end = aggregator.get_previous_week_end(week_end)
    prev_trading_days = aggregator.get_week_trading_days(prev_week_end)

    logger.info(f"Week: {week_start} to {week_end}")
    logger.info(f"Trading days: {len(trading_days)}")

    # Fetch listed info for company names
    listed_info_df = cache.get("listed_info")
    if listed_info_df is None and fetcher:
        listed_info_df = fetcher.fetch_listed_info()

    # Get previous week close for return calculations
    prev_week_quotes = None
    if prev_trading_days:
        prev_last_day = prev_trading_days[-1]
        prev_week_quotes = cache.get(f"daily_quotes_{prev_last_day.strftime('%Y-%m-%d')}")
        if prev_week_quotes is None and fetcher:
            prev_week_quotes = fetcher.fetch_daily_quotes(prev_last_day)

    # Aggregate weekly stock data
    logger.info("Aggregating weekly stock data...")
    weekly_quotes = aggregator.aggregate_daily_quotes(trading_days, prev_week_quotes)

    # Enrich with company info
    if not weekly_quotes.empty and listed_info_df is not None and not listed_info_df.empty:
        info_cols = ["Code", "CompanyName", "Sector33Code", "Sector33CodeName"]
        available_cols = [c for c in info_cols if c in listed_info_df.columns]
        if len(available_cols) > 1:
            weekly_quotes = weekly_quotes.merge(
                listed_info_df[available_cols].drop_duplicates("Code"),
                on="Code",
                how="left",
            )

    # Get previous week index close
    prev_week_indices = None
    if prev_trading_days:
        prev_last_day = prev_trading_days[-1]
        prev_week_indices = cache.get(f"indices_{prev_last_day.strftime('%Y-%m-%d')}")
        if prev_week_indices is None and fetcher:
            prev_week_indices = fetcher.fetch_indices(prev_last_day)

    # Aggregate weekly index data
    logger.info("Aggregating weekly index data...")
    weekly_indices = aggregator.aggregate_indices(trading_days, prev_week_indices)

    # Collect daily index data for daily changes
    daily_indices_list: list[tuple[date, pd.DataFrame]] = []
    for day in trading_days:
        date_str = day.strftime("%Y-%m-%d")
        idx_df = cache.get(f"indices_{date_str}")
        if idx_df is None and fetcher:
            idx_df = fetcher.fetch_indices(day)
        if idx_df is not None and not idx_df.empty:
            daily_indices_list.append((day, idx_df))

    # Aggregate sector performance
    logger.info("Analyzing sector performance...")
    sector_performance = aggregator.aggregate_sector_performance(weekly_quotes)

    # Previous week sector performance for comparison
    prev_week_sector_perf = None
    if prev_trading_days:
        prev_weekly_quotes = aggregator.aggregate_daily_quotes(prev_trading_days, None)
        if not prev_weekly_quotes.empty and listed_info_df is not None:
            info_cols = ["Code", "CompanyName", "Sector33Code", "Sector33CodeName"]
            available_cols = [c for c in info_cols if c in listed_info_df.columns]
            if len(available_cols) > 1:
                prev_weekly_quotes = prev_weekly_quotes.merge(
                    listed_info_df[available_cols].drop_duplicates("Code"),
                    on="Code",
                    how="left",
                )
            prev_week_sector_perf = aggregator.aggregate_sector_performance(prev_weekly_quotes)

    # Get investor trading data
    logger.info("Fetching investor trading data...")
    trades_spec_df = aggregator.get_week_trades_spec(trading_days)
    prev_trades_spec_df = aggregator.get_week_trades_spec(prev_trading_days) if prev_trading_days else None

    # Get margin data
    logger.info("Fetching margin trading data...")
    margin_df = aggregator.get_week_margin_data(week_end)
    prev_margin_df = aggregator.get_week_margin_data(prev_week_end) if prev_week_end else None

    # Get historical data for technical analysis
    logger.info("Fetching historical data...")
    historical_df = aggregator.get_historical_data(trading_days, lookback_weeks=8)

    # Get announcement schedule
    announcements_df = None
    if fetcher:
        announcements_df = fetcher.fetch_announcement()

    # Run weekly analysis
    logger.info("Running weekly analysis...")

    # Section 1: Market Summary
    market_analyzer = WeeklyMarketAnalyzer()
    market_summary = market_analyzer.analyze(
        week_start, week_end, weekly_indices, weekly_quotes, daily_indices_list
    )

    # Section 2: Sector Rotation
    sector_analyzer = WeeklySectorAnalyzer()
    sector_rotation = sector_analyzer.analyze(
        week_end, sector_performance, prev_week_sector_perf
    )

    # Section 3: Performance Rankings
    stock_analyzer = WeeklyStockAnalyzer()
    performance_rankings = stock_analyzer.analyze(week_end, weekly_quotes)

    # Section 4: Investor Activity
    investor_analyzer = WeeklyInvestorAnalyzer()
    investor_activity = investor_analyzer.analyze(
        week_end, trades_spec_df, prev_trades_spec_df
    )

    # Section 5: Margin Trends
    margin_analyzer = WeeklyMarginAnalyzer()
    margin_trends = margin_analyzer.analyze(
        week_end, margin_df, prev_margin_df, weekly_quotes
    )

    # Section 6: Technical Summary
    technical_analyzer = WeeklyTechnicalAnalyzer()
    technical_summary = technical_analyzer.analyze(
        week_end, weekly_quotes, historical_df
    )

    # Section 7: Events Calendar
    events_analyzer = WeeklyEventsAnalyzer()
    events_calendar = events_analyzer.analyze(
        week_end, announcements_df, listed_info_df
    )

    # Section 8: Weekly Topics
    topics_analyzer = WeeklyTopicsAnalyzer()
    weekly_topics = topics_analyzer.analyze(
        week_end, weekly_quotes, sector_performance, historical_df
    )

    # Section 9: Medium-term Trends
    # Collect historical index data for trend analysis
    historical_indices: list[tuple[date, pd.DataFrame]] = []
    for weeks_ago in range(1, 14):
        past_friday = week_end - timedelta(weeks=weeks_ago)
        past_idx = cache.get(f"indices_{past_friday.strftime('%Y-%m-%d')}")
        if past_idx is not None and not past_idx.empty:
            historical_indices.append((past_friday, past_idx))

    # Historical sector performance
    historical_sector_perf: list[tuple[date, pd.DataFrame]] = []
    # We already have current and previous week, skip for now

    trends_analyzer = WeeklyTrendsAnalyzer()
    medium_term_trends = trends_analyzer.analyze(
        week_end, weekly_indices, weekly_quotes,
        historical_indices, historical_sector_perf
    )

    # Generate report
    logger.info("Generating weekly report...")
    generator = WeeklyReportGenerator(output_dir)
    report_path = generator.generate(
        week_start=week_start,
        week_end=week_end,
        market_summary=market_summary,
        sector_rotation=sector_rotation,
        performance_rankings=performance_rankings,
        investor_activity=investor_activity,
        margin_trends=margin_trends,
        technical_summary=technical_summary,
        events_calendar=events_calendar,
        weekly_topics=weekly_topics,
        medium_term_trends=medium_term_trends,
    )

    logger.info(f"Weekly report generated: {report_path}")
    return report_path


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    args = parse_args()

    try:
        config = load_config()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    # Setup logging
    log_level = args.log_level or config.app.log_level
    setup_logging(log_level)
    logger = logging.getLogger(__name__)

    # Determine output directory
    output_dir = Path(args.output_dir) if args.output_dir else config.app.report_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate report
    try:
        if args.weekly:
            # Weekly report mode
            if args.week_end:
                try:
                    week_end = datetime.strptime(args.week_end, "%Y-%m-%d").date()
                except ValueError:
                    logger.error(f"Invalid week-end date format: {args.week_end}. Use YYYY-MM-DD.")
                    return 1
            else:
                week_end = get_latest_friday()

            logger.info(f"Generating weekly report for week ending {week_end}")
            report_path = generate_weekly_report(week_end, args.dry_run, output_dir)
            print(f"Weekly report successfully generated: {report_path}")
        else:
            # Daily report mode
            try:
                target_date = parse_date(args.date)
            except ValueError as e:
                logger.error(str(e))
                return 1

            report_path = generate_report(target_date, args.dry_run, output_dir)
            print(f"Report successfully generated: {report_path}")

        return 0
    except Exception as e:
        logger.exception(f"Failed to generate report: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
