"""Weekly report generator module.

This module generates comprehensive weekly market reports combining
all 9 analysis sections into a formatted Markdown document.
"""

import logging
from datetime import date, datetime
from pathlib import Path

from jinja2 import Template

from jquants_report.report.weekly_templates import WEEKLY_REPORT_TEMPLATE
from jquants_report.report.weekly_types import (
    WeeklyEventsCalendar,
    WeeklyInvestorActivity,
    WeeklyMarginTrends,
    WeeklyMarketSummary,
    WeeklyMediumTermTrends,
    WeeklyPerformanceRankings,
    WeeklySectorRotation,
    WeeklyTechnicalSummary,
    WeeklyTopics,
)

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """Generator for weekly market reports."""

    def __init__(self, output_dir: Path):
        """Initialize WeeklyReportGenerator.

        Args:
            output_dir: Directory for saving generated reports.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        week_start: date,
        week_end: date,
        market_summary: WeeklyMarketSummary,
        sector_rotation: WeeklySectorRotation,
        performance_rankings: WeeklyPerformanceRankings,
        investor_activity: WeeklyInvestorActivity,
        margin_trends: WeeklyMarginTrends,
        technical_summary: WeeklyTechnicalSummary,
        events_calendar: WeeklyEventsCalendar,
        weekly_topics: WeeklyTopics,
        medium_term_trends: WeeklyMediumTermTrends,
    ) -> Path:
        """Generate weekly report.

        Args:
            week_start: Start date of the week.
            week_end: End date of the week.
            market_summary: Section 1 data.
            sector_rotation: Section 2 data.
            performance_rankings: Section 3 data.
            investor_activity: Section 4 data.
            margin_trends: Section 5 data.
            technical_summary: Section 6 data.
            events_calendar: Section 7 data.
            weekly_topics: Section 8 data.
            medium_term_trends: Section 9 data.

        Returns:
            Path to the generated report file.
        """
        logger.info(f"Generating weekly report for {week_start} to {week_end}")

        # Prepare template context
        context = {
            "week_start": week_start.strftime("%Y年%m月%d日"),
            "week_end": week_end.strftime("%Y年%m月%d日"),
            "market_summary": market_summary,
            "sector_rotation": sector_rotation,
            "performance_rankings": performance_rankings,
            "investor_activity": investor_activity,
            "margin_trends": margin_trends,
            "technical_summary": technical_summary,
            "events_calendar": events_calendar,
            "weekly_topics": weekly_topics,
            "medium_term_trends": medium_term_trends,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "enumerate": enumerate,  # Make enumerate available in template
        }

        # Render template
        template = Template(WEEKLY_REPORT_TEMPLATE)
        report_content = template.render(**context)

        # Write to file
        filename = f"weekly_report_{week_end.strftime('%Y%m%d')}.md"
        output_path = self.output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"Weekly report saved to {output_path}")
        return output_path
