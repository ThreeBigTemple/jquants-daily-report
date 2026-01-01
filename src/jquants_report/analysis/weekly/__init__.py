"""Weekly analysis module.

This module provides weekly market analysis functionality for generating
comprehensive weekly reports covering 9 key sections.
"""

from jquants_report.analysis.weekly.events import WeeklyEventsAnalyzer
from jquants_report.analysis.weekly.investor import WeeklyInvestorAnalyzer
from jquants_report.analysis.weekly.margin import WeeklyMarginAnalyzer
from jquants_report.analysis.weekly.market import WeeklyMarketAnalyzer
from jquants_report.analysis.weekly.sector import WeeklySectorAnalyzer
from jquants_report.analysis.weekly.stocks import WeeklyStockAnalyzer
from jquants_report.analysis.weekly.technical import WeeklyTechnicalAnalyzer
from jquants_report.analysis.weekly.topics import WeeklyTopicsAnalyzer
from jquants_report.analysis.weekly.trends import WeeklyTrendsAnalyzer

__all__ = [
    "WeeklyMarketAnalyzer",
    "WeeklySectorAnalyzer",
    "WeeklyStockAnalyzer",
    "WeeklyInvestorAnalyzer",
    "WeeklyMarginAnalyzer",
    "WeeklyTechnicalAnalyzer",
    "WeeklyEventsAnalyzer",
    "WeeklyTopicsAnalyzer",
    "WeeklyTrendsAnalyzer",
]
