"""Data formatting utilities for report generation."""

from datetime import date
from typing import Any


def format_number(value: float | int | None, decimals: int = 0) -> str:
    """Format number with thousand separators.

    Args:
        value: The number to format.
        decimals: Number of decimal places.

    Returns:
        Formatted number string with comma separators.

    Examples:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.567, 2)
        '1,234.57'
        >>> format_number(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    if decimals == 0:
        return f"{int(value):,}"
    else:
        return f"{value:,.{decimals}f}"


def format_percentage(value: float | None, decimals: int = 2) -> str:
    """Format percentage with sign.

    Args:
        value: The percentage value (e.g., 1.5 for 1.5%).
        decimals: Number of decimal places.

    Returns:
        Formatted percentage string with % sign and +/- prefix.

    Examples:
        >>> format_percentage(1.5)
        '+1.50%'
        >>> format_percentage(-2.3, 1)
        '-2.3%'
        >>> format_percentage(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}%"


def format_change(value: float | None, decimals: int = 2) -> str:
    """Format change value with sign.

    Args:
        value: The change value.
        decimals: Number of decimal places.

    Returns:
        Formatted change string with +/- prefix.

    Examples:
        >>> format_change(123.45)
        '+123.45'
        >>> format_change(-67.89, 1)
        '-67.9'
        >>> format_change(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.{decimals}f}"


def format_date(value: date) -> str:
    """Format date in Japanese style.

    Args:
        value: The date to format.

    Returns:
        Formatted date string in YYYY年MM月DD日 format.

    Examples:
        >>> from datetime import date
        >>> format_date(date(2024, 1, 15))
        '2024年01月15日'
    """
    return value.strftime("%Y年%m月%d日")


def format_volume(value: float | int | None) -> str:
    """Format trading volume in human-readable format.

    Args:
        value: The volume value.

    Returns:
        Formatted volume string with unit (万株, 億株).

    Examples:
        >>> format_volume(1234567)
        '123.5万株'
        >>> format_volume(123456789)
        '1.2億株'
        >>> format_volume(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    # Convert to 万株 (10,000 shares)
    man = value / 10000
    if man >= 10000:
        # Convert to 億株 (100,000,000 shares)
        oku = man / 10000
        return f"{oku:.1f}億株"
    else:
        return f"{man:.1f}万株"


def format_amount(value: float | int | None) -> str:
    """Format monetary amount in human-readable format.

    Args:
        value: The amount value in yen.

    Returns:
        Formatted amount string with unit (万円, 億円, 兆円).

    Examples:
        >>> format_amount(12345678)
        '1,234.6万円'
        >>> format_amount(1234567890)
        '12.3億円'
        >>> format_amount(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    # Convert to 万円 (10,000 yen)
    man = value / 10000
    if man >= 100000000:
        # Convert to 兆円 (1,000,000,000,000 yen)
        cho = man / 100000000
        return f"{cho:.1f}兆円"
    elif man >= 10000:
        # Convert to 億円 (100,000,000 yen)
        oku = man / 10000
        return f"{oku:.1f}億円"
    else:
        return f"{man:,.1f}万円"


def format_table_row(values: list[Any], widths: list[int] | None = None) -> str:
    """Format a table row with proper alignment.

    Args:
        values: List of cell values.
        widths: Optional list of column widths.

    Returns:
        Formatted table row string in Markdown format.

    Examples:
        >>> format_table_row(['Code', 'Name', 'Change'])
        '| Code | Name | Change |'
        >>> format_table_row(['1234', 'Company', '+5.2%'], [6, 20, 8])
        '| 1234   | Company              | +5.2%    |'
    """
    if widths:
        cells = [f" {str(val):<{width}} " for val, width in zip(values, widths)]
    else:
        cells = [f" {str(val)} " for val in values]

    return "|" + "|".join(cells) + "|"


def format_table_separator(widths: list[int]) -> str:
    """Format a table separator row.

    Args:
        widths: List of column widths.

    Returns:
        Formatted table separator string in Markdown format.

    Examples:
        >>> format_table_separator([6, 20, 8])
        '|--------|----------------------|----------|'
    """
    cells = ["-" * (width + 2) for width in widths]
    return "|" + "|".join(cells) + "|"


def create_markdown_table(
    headers: list[str],
    rows: list[list[Any]],
    alignments: list[str] | None = None,
) -> str:
    """Create a Markdown table from headers and rows.

    Args:
        headers: List of column headers.
        rows: List of rows, each row is a list of cell values.
        alignments: Optional list of alignments ('left', 'center', 'right').

    Returns:
        Complete Markdown table string.

    Examples:
        >>> headers = ['Code', 'Name', 'Change']
        >>> rows = [['1234', 'Company A', '+5.2%'], ['5678', 'Company B', '-3.1%']]
        >>> print(create_markdown_table(headers, rows))
        | Code | Name | Change |
        |------|------|--------|
        | 1234 | Company A | +5.2% |
        | 5678 | Company B | -3.1% |
    """
    if not rows:
        return ""

    # Convert all cells to strings
    str_headers = [str(h) for h in headers]
    str_rows = [[str(cell) for cell in row] for row in rows]

    # Calculate column widths
    widths = [len(h) for h in str_headers]
    for row in str_rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # Build table
    lines = []

    # Header row
    lines.append(format_table_row(str_headers, widths))

    # Separator row
    if alignments:
        sep_cells = []
        for i, (width, align) in enumerate(zip(widths, alignments)):
            if align == "center":
                sep_cells.append(f":{'-' * width}:")
            elif align == "right":
                sep_cells.append(f"{'-' * width}:")
            else:  # left
                sep_cells.append(f":{'-' * width}")
        lines.append("|" + "|".join(sep_cells) + "|")
    else:
        lines.append(format_table_separator(widths))

    # Data rows
    for row in str_rows:
        lines.append(format_table_row(row, widths))

    return "\n".join(lines)


def format_trend_indicator(value: float | None) -> str:
    """Format trend indicator with arrow symbol.

    Args:
        value: The change value.

    Returns:
        Trend indicator string with arrow (↑/↓/→).

    Examples:
        >>> format_trend_indicator(5.2)
        '↑'
        >>> format_trend_indicator(-3.1)
        '↓'
        >>> format_trend_indicator(0)
        '→'
        >>> format_trend_indicator(None)
        '-'
    """
    if value is None:
        return "-"

    if value > 0:
        return "↑"
    elif value < 0:
        return "↓"
    else:
        return "→"


def format_strength_indicator(
    value: float | None, thresholds: tuple[float, float] = (30, 70)
) -> str:
    """Format strength indicator based on thresholds.

    Args:
        value: The strength value (typically 0-100).
        thresholds: Tuple of (low, high) threshold values.

    Returns:
        Strength indicator string (強い/弱い/中立).

    Examples:
        >>> format_strength_indicator(80)
        '強い'
        >>> format_strength_indicator(20)
        '弱い'
        >>> format_strength_indicator(50)
        '中立'
        >>> format_strength_indicator(None)
        'N/A'
    """
    if value is None:
        return "N/A"

    low, high = thresholds
    if value >= high:
        return "強い"
    elif value <= low:
        return "弱い"
    else:
        return "中立"
