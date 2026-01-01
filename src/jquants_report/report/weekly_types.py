"""Data types for weekly report generation.

This module defines dataclasses for the 9 sections of the weekly report:
1. Weekly Market Summary
2. Sector Rotation
3. Performance Rankings
4. Investor Trading Activity
5. Margin Trading Trends
6. Technical Summary
7. Earnings/Events Calendar
8. Weekly Topics
9. Medium-term Trend Check
"""

from dataclasses import dataclass, field
from datetime import date


# Section 1: Weekly Market Summary
@dataclass
class WeeklyIndexData:
    """Weekly index performance data."""

    name: str
    week_open: float
    week_high: float
    week_low: float
    week_close: float
    weekly_change: float
    weekly_change_pct: float


@dataclass
class DailyIndexChange:
    """Daily index change data for the week."""

    date: date
    close: float
    change: float
    change_pct: float


@dataclass
class WeeklyMarketSummary:
    """Section 1: Weekly market summary data."""

    week_start: date
    week_end: date
    indices: list[WeeklyIndexData]
    daily_changes: dict[str, list[DailyIndexChange]]  # index_name -> daily changes
    total_advancing: int = 0
    total_declining: int = 0
    total_unchanged: int = 0
    week_total_volume: float = 0.0
    week_total_turnover: float = 0.0


# Section 2: Sector Rotation
@dataclass
class SectorRotationData:
    """Sector performance data for rotation analysis."""

    sector_code: str
    sector_name: str
    weekly_return_pct: float
    prev_week_return_pct: float | None = None
    return_change: float | None = None  # This week - last week
    turnover: float = 0.0
    stock_count: int = 0
    advancing_count: int = 0
    declining_count: int = 0


@dataclass
class WeeklySectorRotation:
    """Section 2: Sector rotation analysis."""

    week_end: date
    top_sectors: list[SectorRotationData]  # Top 5 performing
    bottom_sectors: list[SectorRotationData]  # Bottom 5 performing
    all_sectors: list[SectorRotationData]


# Section 3: Performance Rankings
@dataclass
class WeeklyStockPerformance:
    """Individual stock weekly performance."""

    code: str
    name: str
    sector_name: str
    week_open: float
    week_close: float
    weekly_return_pct: float
    week_volume: int
    week_turnover: float
    week_high: float | None = None
    week_low: float | None = None
    prev_week_close: float | None = None


@dataclass
class WeeklyPerformanceRankings:
    """Section 3: Performance rankings."""

    week_end: date
    top_gainers: list[WeeklyStockPerformance]  # Top 10
    top_losers: list[WeeklyStockPerformance]  # Top 10
    top_volume: list[WeeklyStockPerformance]  # Top 10 by volume
    top_turnover: list[WeeklyStockPerformance]  # Top 10 by turnover


# Section 4: Investor Trading Activity
@dataclass
class InvestorCategory:
    """Trading data for an investor category."""

    category_name: str
    buy_value: float
    sell_value: float
    net_value: float  # buy - sell
    prev_week_net: float | None = None
    net_change: float | None = None


@dataclass
class WeeklyInvestorActivity:
    """Section 4: Investor trading activity."""

    week_end: date
    categories: list[InvestorCategory]
    foreigners_net: float = 0.0  # Key metric: foreign investor net
    individuals_net: float = 0.0  # Key metric: individual investor net
    institutions_net: float = 0.0  # Key metric: institutional net


# Section 5: Margin Trading Trends
@dataclass
class MarginTradingData:
    """Margin trading balance and trend data."""

    week_end: date
    margin_buy_balance: float
    margin_sell_balance: float
    margin_ratio: float  # buy/sell
    prev_week_buy_balance: float | None = None
    prev_week_sell_balance: float | None = None
    buy_balance_change: float | None = None
    sell_balance_change: float | None = None


@dataclass
class TopMarginStock:
    """Stock with high margin trading activity."""

    code: str
    name: str
    margin_buy_balance: float
    margin_sell_balance: float
    margin_ratio: float
    weekly_return_pct: float | None = None


@dataclass
class WeeklyMarginTrends:
    """Section 5: Margin trading trends."""

    week_end: date
    overall: MarginTradingData
    top_margin_buy: list[TopMarginStock] = field(default_factory=list)
    top_margin_sell: list[TopMarginStock] = field(default_factory=list)


# Section 6: Technical Summary
@dataclass
class TechnicalIndicatorData:
    """Technical indicator value and signal."""

    name: str
    value: float
    signal: str  # "買い", "売り", "中立" etc.
    prev_week_value: float | None = None
    change: float | None = None


@dataclass
class MovingAverageStatus:
    """Moving average analysis status."""

    period: int  # 25, 75, 200
    stocks_above_pct: float
    trend: str  # "上昇", "下落", "横ばい"
    prev_week_pct: float | None = None


@dataclass
class WeeklyTechnicalSummary:
    """Section 6: Technical analysis summary."""

    week_end: date
    advance_decline_ratio: TechnicalIndicatorData | None = None
    new_highs_count: int = 0
    new_lows_count: int = 0
    moving_averages: list[MovingAverageStatus] = field(default_factory=list)
    rsi_market: TechnicalIndicatorData | None = None  # Market-wide RSI


# Section 7: Earnings/Events Calendar
@dataclass
class EarningsEvent:
    """Scheduled earnings announcement."""

    date: date
    code: str
    name: str
    fiscal_period: str  # "2024年3月期" etc.
    announcement_type: str  # "決算", "業績修正" etc.


@dataclass
class MarketEvent:
    """Other market events (IPO, delisting, etc.)."""

    date: date
    event_type: str  # "IPO", "上場廃止", "株式分割" etc.
    code: str | None
    name: str | None
    description: str


@dataclass
class WeeklyEventsCalendar:
    """Section 7: Events calendar for next week."""

    upcoming_week_start: date
    upcoming_week_end: date
    earnings_announcements: list[EarningsEvent] = field(default_factory=list)
    market_events: list[MarketEvent] = field(default_factory=list)
    key_dates: list[str] = field(default_factory=list)  # Holiday notices, etc.


# Section 8: Weekly Topics
@dataclass
class MarketTopic:
    """Notable market topic/theme for the week."""

    title: str
    description: str
    related_codes: list[str] = field(default_factory=list)
    impact: str = "中立"  # "ポジティブ", "ネガティブ", "中立"


@dataclass
class PriceMovementHighlight:
    """Notable price movement highlight."""

    code: str
    name: str
    movement_type: str  # "ストップ高", "ストップ安", "年初来高値", etc.
    price: float
    change_pct: float
    reason: str | None = None


@dataclass
class WeeklyTopics:
    """Section 8: Weekly topics and highlights."""

    week_end: date
    market_topics: list[MarketTopic] = field(default_factory=list)
    price_highlights: list[PriceMovementHighlight] = field(default_factory=list)
    year_high_low_stocks: list[PriceMovementHighlight] = field(default_factory=list)
    sector_highlights: list[str] = field(default_factory=list)  # Notable sector moves


# Section 9: Medium-term Trend Check
@dataclass
class TrendData:
    """Trend data for a specific period."""

    period_name: str  # "1週間", "1ヶ月", "3ヶ月"
    start_value: float
    end_value: float
    change: float
    change_pct: float
    trend_direction: str  # "上昇", "下落", "横ばい"


@dataclass
class SectorTrendData:
    """Sector trend over medium term."""

    sector_name: str
    one_week_return: float
    one_month_return: float | None = None
    three_month_return: float | None = None
    trend_strength: str = "中立"  # "強気", "弱気", "中立"


@dataclass
class WeeklyMediumTermTrends:
    """Section 9: Medium-term trend confirmation."""

    week_end: date
    index_trends: dict[str, list[TrendData]]  # index_name -> trends by period
    sector_trends: list[SectorTrendData] = field(default_factory=list)
    market_breadth_trend: str = "中立"  # Overall market trend assessment
    outlook_summary: str = ""  # Brief outlook summary


# Complete Weekly Report
@dataclass
class WeeklyReport:
    """Complete weekly report containing all 9 sections."""

    week_start: date
    week_end: date
    market_summary: WeeklyMarketSummary
    sector_rotation: WeeklySectorRotation
    performance_rankings: WeeklyPerformanceRankings
    investor_activity: WeeklyInvestorActivity
    margin_trends: WeeklyMarginTrends
    technical_summary: WeeklyTechnicalSummary
    events_calendar: WeeklyEventsCalendar
    weekly_topics: WeeklyTopics
    medium_term_trends: WeeklyMediumTermTrends
