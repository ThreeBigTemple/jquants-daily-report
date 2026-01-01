"""Jinja2 templates for report generation."""

from jinja2 import BaseLoader, Environment

# Main report template
MAIN_TEMPLATE = """# 日次株式市場レポート - {{ report_date }}

## 1. 市場全体の概況

### 主要指数
{{ market_overview }}

### 騰落銘柄数
{{ market_breadth }}

### 市場コメント
{{ market_comment }}

---

## 2. セクター分析

### セクター別騰落率
{{ sector_performance }}

### セクター別売買代金
{{ sector_turnover }}

### セクターコメント
{{ sector_comment }}

---

## 3. 個別銘柄ハイライト

### 値上がり率上位
{{ top_gainers }}

### 値下がり率上位
{{ top_losers }}

### 出来高上位
{{ top_volume }}

### 売買代金上位
{{ top_turnover }}

---

## 4. 需給分析

### 信用残高
{{ margin_balance }}

### 空売り比率
{{ short_selling }}

### 需給コメント
{{ supply_demand_comment }}

---

## 5. テクニカル指標サマリー

### 移動平均線
{{ moving_averages }}

### モメンタム指標
{{ momentum_indicators }}

### テクニカルコメント
{{ technical_comment }}

---

## 6. 翌営業日の注目点

{{ next_day_focus }}

---

*このレポートはJ-Quants APIを使用して自動生成されました。*
"""


def get_template_environment() -> Environment:
    """Get Jinja2 environment with custom filters.

    Returns:
        Configured Jinja2 Environment instance.
    """
    from jquants_report.report.formatter import (
        format_amount,
        format_change,
        format_date,
        format_number,
        format_percentage,
        format_strength_indicator,
        format_trend_indicator,
        format_volume,
    )

    env = Environment(loader=BaseLoader())

    # Register custom filters
    env.filters["format_number"] = format_number
    env.filters["format_percentage"] = format_percentage
    env.filters["format_change"] = format_change
    env.filters["format_date"] = format_date
    env.filters["format_volume"] = format_volume
    env.filters["format_amount"] = format_amount
    env.filters["format_trend"] = format_trend_indicator
    env.filters["format_strength"] = format_strength_indicator

    return env


def render_main_template(**kwargs: str) -> str:
    """Render the main report template.

    Args:
        **kwargs: Template variables including:
            - report_date: Report date string
            - market_overview: Market overview section
            - market_breadth: Market breadth section
            - market_comment: Market commentary
            - sector_performance: Sector performance table
            - sector_turnover: Sector turnover table
            - sector_comment: Sector commentary
            - top_gainers: Top gainers table
            - top_losers: Top losers table
            - top_volume: Top volume table
            - top_turnover: Top turnover table
            - margin_balance: Margin balance section
            - short_selling: Short selling section
            - supply_demand_comment: Supply/demand commentary
            - moving_averages: Moving averages section
            - momentum_indicators: Momentum indicators section
            - technical_comment: Technical commentary
            - next_day_focus: Next day focus points

    Returns:
        Rendered report string.
    """
    env = get_template_environment()
    template = env.from_string(MAIN_TEMPLATE)
    return template.render(**kwargs)
