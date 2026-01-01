"""Weekly events calendar module.

Section 7: Earnings/Events Calendar
- Upcoming earnings announcements
- IPOs and delistings
- Other market events
"""

import logging
from datetime import date, timedelta

import pandas as pd

from jquants_report.report.weekly_types import (
    EarningsEvent,
    WeeklyEventsCalendar,
)

logger = logging.getLogger(__name__)


class WeeklyEventsAnalyzer:
    """Analyzer for weekly events calendar (Section 7)."""

    def analyze(
        self,
        week_end: date,
        announcements_df: pd.DataFrame | None = None,
        listed_info_df: pd.DataFrame | None = None,
    ) -> WeeklyEventsCalendar:
        """Analyze upcoming events for next week.

        Args:
            week_end: End date of the current week.
            announcements_df: Earnings announcement schedule.
            listed_info_df: Listed company info for names.

        Returns:
            WeeklyEventsCalendar: Events calendar for next week.
        """
        # Calculate next week dates
        next_monday = week_end + timedelta(days=(7 - week_end.weekday()))
        next_friday = next_monday + timedelta(days=4)

        # Process earnings announcements
        earnings = self._process_earnings(
            announcements_df,
            next_monday,
            next_friday,
            listed_info_df,
        )

        # Generate key dates (holidays, etc.)
        key_dates = self._get_key_dates(next_monday, next_friday)

        return WeeklyEventsCalendar(
            upcoming_week_start=next_monday,
            upcoming_week_end=next_friday,
            earnings_announcements=earnings,
            market_events=[],  # Can be extended for IPOs, etc.
            key_dates=key_dates,
        )

    def _process_earnings(
        self,
        announcements_df: pd.DataFrame | None,
        start_date: date,
        end_date: date,
        listed_info_df: pd.DataFrame | None,
    ) -> list[EarningsEvent]:
        """Process earnings announcements for the period."""
        if announcements_df is None or announcements_df.empty:
            return []

        events = []

        # Create name lookup
        name_lookup: dict[str, str] = {}
        if listed_info_df is not None and not listed_info_df.empty:
            for _, row in listed_info_df.iterrows():
                code = str(row.get("Code", ""))
                name = str(row.get("CompanyName", ""))
                if code and name:
                    name_lookup[code] = name

        # Filter announcements for date range
        for _, row in announcements_df.iterrows():
            ann_date_str = str(row.get("Date", row.get("AnnouncementDate", "")))
            if not ann_date_str:
                continue

            try:
                ann_date = date.fromisoformat(ann_date_str[:10])
            except ValueError:
                continue

            if not (start_date <= ann_date <= end_date):
                continue

            code = str(row.get("Code", ""))
            name = name_lookup.get(code, str(row.get("CompanyName", "不明")))

            # Determine fiscal period
            fiscal_period = str(row.get("FiscalPeriodEnd", row.get("Period", "不明")))

            # Determine announcement type
            ann_type = "決算発表"
            if "Revision" in str(row.get("Type", "")):
                ann_type = "業績修正"
            elif "Interim" in str(row.get("Type", "")):
                ann_type = "中間決算"
            elif "Q1" in str(row.get("Type", "")) or "Q3" in str(row.get("Type", "")):
                ann_type = "四半期決算"

            events.append(
                EarningsEvent(
                    date=ann_date,
                    code=code,
                    name=name,
                    fiscal_period=fiscal_period,
                    announcement_type=ann_type,
                )
            )

        # Sort by date
        events.sort(key=lambda x: x.date)

        return events

    def _get_key_dates(self, start_date: date, end_date: date) -> list[str]:
        """Get key dates for the period (holidays, special dates)."""
        key_dates = []

        # Japanese holidays (simplified - a full implementation would use a holiday library)
        japanese_holidays = {
            (1, 1): "元日",
            (1, 2): "振替休日（年始）",
            (1, 3): "年始休暇",
            (2, 11): "建国記念の日",
            (2, 23): "天皇誕生日",
            (3, 21): "春分の日",  # Approximate
            (4, 29): "昭和の日",
            (5, 3): "憲法記念日",
            (5, 4): "みどりの日",
            (5, 5): "こどもの日",
            (7, 20): "海の日",  # Third Monday
            (8, 11): "山の日",
            (9, 16): "敬老の日",  # Third Monday
            (9, 23): "秋分の日",  # Approximate
            (10, 14): "スポーツの日",  # Second Monday
            (11, 3): "文化の日",
            (11, 23): "勤労感謝の日",
        }

        current = start_date
        while current <= end_date:
            key = (current.month, current.day)
            if key in japanese_holidays:
                holiday_name = japanese_holidays[key]
                key_dates.append(f"{current.month}/{current.day}（{current.strftime('%a')}）: {holiday_name}（休場）")
            current += timedelta(days=1)

        # Year-end/New Year warnings
        if start_date.month == 12 and start_date.day >= 25:
            key_dates.append("年末年始の取引時間にご注意ください")

        return key_dates
