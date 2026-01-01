"""Report generation module."""

from jquants_report.report.generator import (
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
from jquants_report.report.weekly_generator import WeeklyReportGenerator
from jquants_report.report.weekly_types import (
    WeeklyEventsCalendar,
    WeeklyIndexData,
    WeeklyInvestorActivity,
    WeeklyMarginTrends,
    WeeklyMarketSummary,
    WeeklyMediumTermTrends,
    WeeklyPerformanceRankings,
    WeeklyReport,
    WeeklySectorRotation,
    WeeklyTechnicalSummary,
    WeeklyTopics,
)

__all__ = [
    # Daily report
    "ReportGenerator",
    "MarketSummary",
    "IndexData",
    "SectorAnalysis",
    "SectorData",
    "StockHighlights",
    "StockData",
    "TechnicalSummary",
    "TechnicalIndicator",
    "SupplyDemandSummary",
    # Weekly report
    "WeeklyReportGenerator",
    "WeeklyReport",
    "WeeklyMarketSummary",
    "WeeklyIndexData",
    "WeeklySectorRotation",
    "WeeklyPerformanceRankings",
    "WeeklyInvestorActivity",
    "WeeklyMarginTrends",
    "WeeklyTechnicalSummary",
    "WeeklyEventsCalendar",
    "WeeklyTopics",
    "WeeklyMediumTermTrends",
]
