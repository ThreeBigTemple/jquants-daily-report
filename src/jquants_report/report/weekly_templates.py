"""Jinja2 templates for weekly report generation."""

WEEKLY_REPORT_TEMPLATE = """# 週次株式市場レポート

**対象期間**: {{ week_start }} 〜 {{ week_end }}

---

## 1. 週間市場サマリー

### 主要指数パフォーマンス

| 指数 | 週初 | 週高値 | 週安値 | 週末終値 | 週間変動 | 週間騰落率 |
|:-----|------:|-------:|-------:|---------:|---------:|----------:|
{% for idx in market_summary.indices -%}
| {{ idx.name }} | {{ "{:,.2f}".format(idx.week_open) }} | {{ "{:,.2f}".format(idx.week_high) }} | {{ "{:,.2f}".format(idx.week_low) }} | {{ "{:,.2f}".format(idx.week_close) }} | {{ "{:+,.2f}".format(idx.weekly_change) }} | {{ "{:+.2f}".format(idx.weekly_change_pct) }}% |
{% endfor %}

### 日次推移
{% for idx_name, daily_list in market_summary.daily_changes.items() %}
#### {{ idx_name }}
| 日付 | 終値 | 前日比 | 騰落率 |
|:-----|-----:|-------:|-------:|
{% for day in daily_list -%}
| {{ day.date.strftime('%m/%d') }} | {{ "{:,.2f}".format(day.close) }} | {{ "{:+,.2f}".format(day.change) }} | {{ "{:+.2f}".format(day.change_pct) }}% |
{% endfor %}
{% endfor %}

### 週間騰落状況

| 項目 | 銘柄数 | 比率 |
|:-----|-------:|-----:|
| 値上がり | {{ "{:,}".format(market_summary.total_advancing) }} | {{ "{:.1f}".format(market_summary.total_advancing / (market_summary.total_advancing + market_summary.total_declining + market_summary.total_unchanged) * 100 if (market_summary.total_advancing + market_summary.total_declining + market_summary.total_unchanged) > 0 else 0) }}% |
| 値下がり | {{ "{:,}".format(market_summary.total_declining) }} | {{ "{:.1f}".format(market_summary.total_declining / (market_summary.total_advancing + market_summary.total_declining + market_summary.total_unchanged) * 100 if (market_summary.total_advancing + market_summary.total_declining + market_summary.total_unchanged) > 0 else 0) }}% |
| 変わらず | {{ "{:,}".format(market_summary.total_unchanged) }} | {{ "{:.1f}".format(market_summary.total_unchanged / (market_summary.total_advancing + market_summary.total_declining + market_summary.total_unchanged) * 100 if (market_summary.total_advancing + market_summary.total_declining + market_summary.total_unchanged) > 0 else 0) }}% |

**週間売買代金**: {{ "{:,.0f}".format(market_summary.week_total_turnover / 100000000) }}億円

---

## 2. セクターローテーション分析

### 週間パフォーマンス上位5セクター

| 順位 | セクター | 週間騰落率 | 前週比 | 売買代金 | 銘柄数 |
|:----:|:---------|----------:|-------:|---------:|-------:|
{% for i, sector in enumerate(sector_rotation.top_sectors, 1) -%}
| {{ i }} | {{ sector.sector_name }} | {{ "{:+.2f}".format(sector.weekly_return_pct) }}% | {{ "{:+.2f}".format(sector.return_change) if sector.return_change is not none else "N/A" }}pt | {{ "{:,.0f}".format(sector.turnover / 100000000) }}億円 | {{ sector.stock_count }} |
{% endfor %}

### 週間パフォーマンス下位5セクター

| 順位 | セクター | 週間騰落率 | 前週比 | 売買代金 | 銘柄数 |
|:----:|:---------|----------:|-------:|---------:|-------:|
{% for i, sector in enumerate(sector_rotation.bottom_sectors, 1) -%}
| {{ i }} | {{ sector.sector_name }} | {{ "{:+.2f}".format(sector.weekly_return_pct) }}% | {{ "{:+.2f}".format(sector.return_change) if sector.return_change is not none else "N/A" }}pt | {{ "{:,.0f}".format(sector.turnover / 100000000) }}億円 | {{ sector.stock_count }} |
{% endfor %}

---

## 3. 週間パフォーマンスランキング

### 値上がり率上位10銘柄

| 順位 | コード | 銘柄名 | セクター | 週末終値 | 週間騰落率 |
|:----:|:------:|:-------|:---------|--------:|----------:|
{% for i, stock in enumerate(performance_rankings.top_gainers, 1) -%}
| {{ i }} | {{ stock.code }} | {{ stock.name[:12] }}{% if stock.name|length > 12 %}...{% endif %} | {{ stock.sector_name[:8] }} | {{ "{:,.0f}".format(stock.week_close) }} | {{ "{:+.2f}".format(stock.weekly_return_pct) }}% |
{% endfor %}

### 値下がり率上位10銘柄

| 順位 | コード | 銘柄名 | セクター | 週末終値 | 週間騰落率 |
|:----:|:------:|:-------|:---------|--------:|----------:|
{% for i, stock in enumerate(performance_rankings.top_losers, 1) -%}
| {{ i }} | {{ stock.code }} | {{ stock.name[:12] }}{% if stock.name|length > 12 %}...{% endif %} | {{ stock.sector_name[:8] }} | {{ "{:,.0f}".format(stock.week_close) }} | {{ "{:+.2f}".format(stock.weekly_return_pct) }}% |
{% endfor %}

### 売買代金上位10銘柄

| 順位 | コード | 銘柄名 | 週間売買代金 | 週間騰落率 |
|:----:|:------:|:-------|------------:|----------:|
{% for i, stock in enumerate(performance_rankings.top_turnover, 1) -%}
| {{ i }} | {{ stock.code }} | {{ stock.name[:15] }}{% if stock.name|length > 15 %}...{% endif %} | {{ "{:,.0f}".format(stock.week_turnover / 100000000) }}億円 | {{ "{:+.2f}".format(stock.weekly_return_pct) }}% |
{% endfor %}

---

## 4. 投資部門別売買動向

{% if investor_activity.categories %}
| 投資主体 | 買い | 売り | 差引 | 前週差引 | 変化 |
|:---------|-----:|-----:|-----:|---------:|-----:|
{% for cat in investor_activity.categories -%}
| {{ cat.category_name }} | {{ "{:,.0f}".format(cat.buy_value / 100000000) }}億円 | {{ "{:,.0f}".format(cat.sell_value / 100000000) }}億円 | {{ "{:+,.0f}".format(cat.net_value / 100000000) }}億円 | {{ "{:+,.0f}".format(cat.prev_week_net / 100000000) if cat.prev_week_net is not none else "N/A" }}億円 | {{ "{:+,.0f}".format(cat.net_change / 100000000) if cat.net_change is not none else "N/A" }}億円 |
{% endfor %}

### 主要投資主体の動向

- **外国人投資家**: {{ "{:+,.0f}".format(investor_activity.foreigners_net / 100000000) }}億円の{% if investor_activity.foreigners_net > 0 %}買い越し{% elif investor_activity.foreigners_net < 0 %}売り越し{% else %}均衡{% endif %}
- **個人投資家**: {{ "{:+,.0f}".format(investor_activity.individuals_net / 100000000) }}億円の{% if investor_activity.individuals_net > 0 %}買い越し{% elif investor_activity.individuals_net < 0 %}売り越し{% else %}均衡{% endif %}
- **機関投資家**: {{ "{:+,.0f}".format(investor_activity.institutions_net / 100000000) }}億円の{% if investor_activity.institutions_net > 0 %}買い越し{% elif investor_activity.institutions_net < 0 %}売り越し{% else %}均衡{% endif %}
{% else %}
データがありません。
{% endif %}

---

## 5. 信用取引動向

### 全体概況

| 項目 | 今週 | 前週 | 増減 |
|:-----|-----:|-----:|-----:|
| 信用買い残 | {{ "{:,.0f}".format(margin_trends.overall.margin_buy_balance / 100000000) }}億円 | {{ "{:,.0f}".format(margin_trends.overall.prev_week_buy_balance / 100000000) if margin_trends.overall.prev_week_buy_balance is not none else "N/A" }}億円 | {{ "{:+,.0f}".format(margin_trends.overall.buy_balance_change / 100000000) if margin_trends.overall.buy_balance_change is not none else "N/A" }}億円 |
| 信用売り残 | {{ "{:,.0f}".format(margin_trends.overall.margin_sell_balance / 100000000) }}億円 | {{ "{:,.0f}".format(margin_trends.overall.prev_week_sell_balance / 100000000) if margin_trends.overall.prev_week_sell_balance is not none else "N/A" }}億円 | {{ "{:+,.0f}".format(margin_trends.overall.sell_balance_change / 100000000) if margin_trends.overall.sell_balance_change is not none else "N/A" }}億円 |
| 信用倍率 | {{ "{:.2f}".format(margin_trends.overall.margin_ratio) }}倍 | - | - |

{% if margin_trends.top_margin_buy %}
### 信用買い残上位銘柄

| コード | 銘柄名 | 買い残 | 売り残 | 倍率 | 週間騰落率 |
|:------:|:-------|-------:|-------:|-----:|----------:|
{% for stock in margin_trends.top_margin_buy[:5] -%}
| {{ stock.code }} | {{ stock.name[:12] }} | {{ "{:,.0f}".format(stock.margin_buy_balance / 1000000) }}百万 | {{ "{:,.0f}".format(stock.margin_sell_balance / 1000000) }}百万 | {{ "{:.2f}".format(stock.margin_ratio) }} | {{ "{:+.2f}".format(stock.weekly_return_pct) if stock.weekly_return_pct is not none else "N/A" }}% |
{% endfor %}
{% endif %}

---

## 6. テクニカル指標サマリー

### 騰落レシオ

{% if technical_summary.advance_decline_ratio %}
| 指標 | 今週 | 前週 | 変化 | シグナル |
|:-----|-----:|-----:|-----:|:---------|
| 騰落レシオ | {{ "{:.1f}".format(technical_summary.advance_decline_ratio.value) }}% | {{ "{:.1f}".format(technical_summary.advance_decline_ratio.prev_week_value) if technical_summary.advance_decline_ratio.prev_week_value is not none else "N/A" }}% | {{ "{:+.1f}".format(technical_summary.advance_decline_ratio.change) if technical_summary.advance_decline_ratio.change is not none else "N/A" }}pt | {{ technical_summary.advance_decline_ratio.signal }} |
{% else %}
データがありません。
{% endif %}

### 新高値・新安値銘柄数

| 項目 | 銘柄数 |
|:-----|-------:|
| 年初来高値更新 | {{ technical_summary.new_highs_count }} |
| 年初来安値更新 | {{ technical_summary.new_lows_count }} |

### 移動平均線分析

{% if technical_summary.moving_averages %}
| 期間 | MA上回り比率 | 前週 | トレンド |
|:-----|------------:|-----:|:---------|
{% for ma in technical_summary.moving_averages -%}
| {{ ma.period }}日線 | {{ "{:.1f}".format(ma.stocks_above_pct) }}% | {{ "{:.1f}".format(ma.prev_week_pct) if ma.prev_week_pct is not none else "N/A" }}% | {{ ma.trend }} |
{% endfor %}
{% else %}
データがありません。
{% endif %}

---

## 7. 来週の決算・イベントカレンダー

**対象期間**: {{ events_calendar.upcoming_week_start.strftime('%Y/%m/%d') }} 〜 {{ events_calendar.upcoming_week_end.strftime('%Y/%m/%d') }}

{% if events_calendar.earnings_announcements %}
### 決算発表予定

| 日付 | コード | 銘柄名 | 決算期 | 種別 |
|:-----|:------:|:-------|:-------|:-----|
{% for event in events_calendar.earnings_announcements[:20] -%}
| {{ event.date.strftime('%m/%d') }} | {{ event.code }} | {{ event.name[:15] }} | {{ event.fiscal_period }} | {{ event.announcement_type }} |
{% endfor %}
{% if events_calendar.earnings_announcements|length > 20 %}
*他{{ events_calendar.earnings_announcements|length - 20 }}件の決算発表予定があります。*
{% endif %}
{% else %}
来週の決算発表予定はありません。
{% endif %}

{% if events_calendar.key_dates %}
### 注意事項
{% for note in events_calendar.key_dates %}
- {{ note }}
{% endfor %}
{% endif %}

---

## 8. 週間トピックス

{% if weekly_topics.market_topics %}
### 市場トピック
{% for topic in weekly_topics.market_topics %}
#### {{ topic.title }}
{{ topic.description }}
{% if topic.related_codes %}
*関連銘柄: {{ topic.related_codes|join(', ') }}*
{% endif %}
{% endfor %}
{% endif %}

{% if weekly_topics.price_highlights %}
### 注目の値動き

| コード | 銘柄名 | 種別 | 価格 | 週間騰落率 |
|:------:|:-------|:-----|-----:|----------:|
{% for highlight in weekly_topics.price_highlights[:10] -%}
| {{ highlight.code }} | {{ highlight.name[:15] }} | {{ highlight.movement_type }} | {{ "{:,.0f}".format(highlight.price) }} | {{ "{:+.2f}".format(highlight.change_pct) }}% |
{% endfor %}
{% endif %}

{% if weekly_topics.year_high_low_stocks %}
### 年初来高値・安値銘柄

| コード | 銘柄名 | 種別 | 価格 | 週間騰落率 |
|:------:|:-------|:-----|-----:|----------:|
{% for stock in weekly_topics.year_high_low_stocks[:10] -%}
| {{ stock.code }} | {{ stock.name[:15] }} | {{ stock.movement_type }} | {{ "{:,.0f}".format(stock.price) }} | {{ "{:+.2f}".format(stock.change_pct) }}% |
{% endfor %}
{% endif %}

{% if weekly_topics.sector_highlights %}
### セクターハイライト
{% for highlight in weekly_topics.sector_highlights %}
- {{ highlight }}
{% endfor %}
{% endif %}

---

## 9. 中期トレンド確認

### 指数トレンド

{% for idx_name, trends in medium_term_trends.index_trends.items() %}
#### {{ idx_name }}
{% if trends %}
| 期間 | 期初 | 期末 | 変動 | 騰落率 | 方向 |
|:-----|-----:|-----:|-----:|-------:|:-----|
{% for trend in trends -%}
| {{ trend.period_name }} | {{ "{:,.2f}".format(trend.start_value) }} | {{ "{:,.2f}".format(trend.end_value) }} | {{ "{:+,.2f}".format(trend.change) }} | {{ "{:+.2f}".format(trend.change_pct) }}% | {{ trend.trend_direction }} |
{% endfor %}
{% else %}
データがありません。
{% endif %}
{% endfor %}

### セクター別トレンド（上位10セクター）

{% if medium_term_trends.sector_trends %}
| セクター | 1週間 | 1ヶ月 | 3ヶ月 | 強弱 |
|:---------|------:|------:|------:|:-----|
{% for sector in medium_term_trends.sector_trends[:10] -%}
| {{ sector.sector_name[:10] }} | {{ "{:+.2f}".format(sector.one_week_return) }}% | {{ "{:+.2f}".format(sector.one_month_return) if sector.one_month_return is not none else "N/A" }}% | {{ "{:+.2f}".format(sector.three_month_return) if sector.three_month_return is not none else "N/A" }}% | {{ sector.trend_strength }} |
{% endfor %}
{% else %}
データがありません。
{% endif %}

### 市場見通し

**市場騰落傾向**: {{ medium_term_trends.market_breadth_trend }}

{{ medium_term_trends.outlook_summary }}

---

*レポート生成日時: {{ generated_at }}*
*本レポートはJ-Quants APIのデータに基づいて自動生成されています。投資判断の参考情報としてご利用ください。*
"""
