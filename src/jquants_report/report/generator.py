"""Report generation module."""

import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from jquants_report.report.formatter import (
    create_markdown_table,
    format_amount,
    format_change,
    format_date,
    format_number,
    format_percentage,
    format_trend_indicator,
    format_volume,
)
from jquants_report.report.templates import render_main_template

logger = logging.getLogger(__name__)


@dataclass
class IndexData:
    """Index data."""

    name: str
    close: float
    change: float
    change_pct: float
    volume: int | None = None


@dataclass
class MarketSummary:
    """Market summary data."""

    indices: list[IndexData]
    advancing: int
    declining: int
    unchanged: int
    total_volume: float
    total_turnover: float
    comment: str = ""


@dataclass
class SectorData:
    """Sector data."""

    name: str
    change_pct: float
    turnover: float


@dataclass
class SectorAnalysis:
    """Sector analysis data."""

    sectors: list[SectorData]
    comment: str = ""


@dataclass
class StockData:
    """Stock data."""

    code: str
    name: str
    close: float
    change: float
    change_pct: float
    volume: int
    turnover: float


@dataclass
class StockHighlights:
    """Stock highlights data."""

    top_gainers: list[StockData]
    top_losers: list[StockData]
    top_volume: list[StockData]
    top_turnover: list[StockData]


@dataclass
class TechnicalIndicator:
    """Technical indicator data."""

    name: str
    value: float
    signal: str


@dataclass
class TechnicalSummary:
    """Technical summary data."""

    moving_averages: list[TechnicalIndicator]
    momentum_indicators: list[TechnicalIndicator]
    comment: str = ""


@dataclass
class SupplyDemandSummary:
    """Supply and demand summary data."""

    margin_buying_balance: float
    margin_selling_balance: float
    margin_ratio: float
    short_selling_ratio: float
    comment: str = ""


class ReportGenerator:
    """Generate market reports in Markdown format."""

    def __init__(self, output_dir: Path) -> None:
        """Initialize report generator.

        Args:
            output_dir: Directory to save generated reports.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        target_date: date,
        market_summary: MarketSummary,
        sector_analysis: SectorAnalysis,
        stock_highlights: StockHighlights,
        technical_summary: TechnicalSummary,
        supply_demand: SupplyDemandSummary,
    ) -> Path:
        """Generate market report.

        Args:
            target_date: The target date for the report.
            market_summary: Market summary data.
            sector_analysis: Sector analysis data.
            stock_highlights: Stock highlights data.
            technical_summary: Technical summary data.
            supply_demand: Supply and demand data.

        Returns:
            Path to the generated report file.
        """
        logger.info(f"Generating report for {target_date}")

        # Format each section
        report_date = format_date(target_date)
        market_overview = self._format_market_overview(market_summary)
        market_breadth = self._format_market_breadth(market_summary)
        market_comment = market_summary.comment or self._generate_market_comment(market_summary)

        sector_performance = self._format_sector_performance(sector_analysis)
        sector_turnover = self._format_sector_turnover(sector_analysis)
        sector_comment = sector_analysis.comment or self._generate_sector_comment(sector_analysis)

        top_gainers = self._format_stock_table(stock_highlights.top_gainers)
        top_losers = self._format_stock_table(stock_highlights.top_losers)
        top_volume = self._format_stock_table(stock_highlights.top_volume)
        top_turnover = self._format_stock_table(stock_highlights.top_turnover)

        margin_balance = self._format_margin_balance(supply_demand)
        short_selling = self._format_short_selling(supply_demand)
        supply_demand_comment = supply_demand.comment or self._generate_supply_demand_comment(
            supply_demand
        )

        moving_averages = self._format_technical_indicators(technical_summary.moving_averages)
        momentum_indicators = self._format_technical_indicators(
            technical_summary.momentum_indicators
        )
        technical_comment = technical_summary.comment or self._generate_technical_comment(
            technical_summary
        )

        next_day_focus = self._generate_next_day_focus(
            market_summary, sector_analysis, technical_summary
        )

        # Render template
        report_content = render_main_template(
            report_date=report_date,
            market_overview=market_overview,
            market_breadth=market_breadth,
            market_comment=market_comment,
            sector_performance=sector_performance,
            sector_turnover=sector_turnover,
            sector_comment=sector_comment,
            top_gainers=top_gainers,
            top_losers=top_losers,
            top_volume=top_volume,
            top_turnover=top_turnover,
            margin_balance=margin_balance,
            short_selling=short_selling,
            supply_demand_comment=supply_demand_comment,
            moving_averages=moving_averages,
            momentum_indicators=momentum_indicators,
            technical_comment=technical_comment,
            next_day_focus=next_day_focus,
        )

        # Save to file
        filename = f"market_report_{target_date.strftime('%Y%m%d')}.md"
        report_path = self.output_dir / filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)

        logger.info(f"Report saved to {report_path}")
        return report_path

    def _format_market_overview(self, summary: MarketSummary) -> str:
        """Format market overview section.

        Args:
            summary: Market summary data.

        Returns:
            Formatted market overview string.
        """
        headers = ["指数", "終値", "前日比", "騰落率"]
        rows = []

        for idx in summary.indices:
            rows.append(
                [
                    idx.name,
                    format_number(idx.close, 2),
                    format_change(idx.change, 2) + " " + format_trend_indicator(idx.change),
                    format_percentage(idx.change_pct, 2),
                ]
            )

        return create_markdown_table(
            headers, rows, alignments=["left", "right", "right", "right"]
        )

    def _format_market_breadth(self, summary: MarketSummary) -> str:
        """Format market breadth section.

        Args:
            summary: Market summary data.

        Returns:
            Formatted market breadth string.
        """
        total = summary.advancing + summary.declining + summary.unchanged
        adv_pct = (summary.advancing / total * 100) if total > 0 else 0
        dec_pct = (summary.declining / total * 100) if total > 0 else 0

        headers = ["項目", "銘柄数", "比率"]
        rows = [
            ["値上がり", format_number(summary.advancing), f"{adv_pct:.1f}%"],
            ["値下がり", format_number(summary.declining), f"{dec_pct:.1f}%"],
            ["変わらず", format_number(summary.unchanged), "-"],
        ]

        table = create_markdown_table(headers, rows, alignments=["left", "right", "right"])

        # Add summary statistics
        summary_text = f"\n\n- **総売買代金**: {format_amount(summary.total_turnover)}\n"
        summary_text += f"- **総出来高**: {format_volume(summary.total_volume)}"

        return table + summary_text

    def _format_sector_performance(self, analysis: SectorAnalysis) -> str:
        """Format sector performance table.

        Args:
            analysis: Sector analysis data.

        Returns:
            Formatted sector performance table.
        """
        # Sort by change percentage descending
        sorted_sectors = sorted(analysis.sectors, key=lambda s: s.change_pct, reverse=True)

        headers = ["セクター", "騰落率", "トレンド"]
        rows = []

        for sector in sorted_sectors:
            rows.append(
                [
                    sector.name,
                    format_percentage(sector.change_pct, 2),
                    format_trend_indicator(sector.change_pct),
                ]
            )

        return create_markdown_table(headers, rows, alignments=["left", "right", "center"])

    def _format_sector_turnover(self, analysis: SectorAnalysis) -> str:
        """Format sector turnover table.

        Args:
            analysis: Sector analysis data.

        Returns:
            Formatted sector turnover table.
        """
        # Sort by turnover descending
        sorted_sectors = sorted(analysis.sectors, key=lambda s: s.turnover, reverse=True)

        headers = ["セクター", "売買代金"]
        rows = []

        for sector in sorted_sectors[:10]:  # Top 10
            rows.append([sector.name, format_amount(sector.turnover)])

        return create_markdown_table(headers, rows, alignments=["left", "right"])

    def _format_stock_table(self, stocks: list[StockData]) -> str:
        """Format stock table.

        Args:
            stocks: List of stock data.

        Returns:
            Formatted stock table.
        """
        if not stocks:
            return "データがありません。"

        headers = ["コード", "銘柄名", "終値", "前日比", "騰落率", "出来高", "売買代金"]
        rows = []

        for stock in stocks:
            rows.append(
                [
                    stock.code,
                    stock.name,
                    format_number(stock.close, 0),
                    format_change(stock.change, 0) + " " + format_trend_indicator(stock.change),
                    format_percentage(stock.change_pct, 2),
                    format_volume(stock.volume),
                    format_amount(stock.turnover),
                ]
            )

        return create_markdown_table(
            headers,
            rows,
            alignments=["left", "left", "right", "right", "right", "right", "right"],
        )

    def _format_margin_balance(self, supply_demand: SupplyDemandSummary) -> str:
        """Format margin balance section.

        Args:
            supply_demand: Supply and demand data.

        Returns:
            Formatted margin balance string.
        """
        headers = ["項目", "残高", "比率"]
        rows = [
            [
                "信用買い残",
                format_amount(supply_demand.margin_buying_balance),
                format_percentage(supply_demand.margin_ratio, 2),
            ],
            ["信用売り残", format_amount(supply_demand.margin_selling_balance), "-"],
        ]

        return create_markdown_table(headers, rows, alignments=["left", "right", "right"])

    def _format_short_selling(self, supply_demand: SupplyDemandSummary) -> str:
        """Format short selling section.

        Args:
            supply_demand: Supply and demand data.

        Returns:
            Formatted short selling string.
        """
        return f"- **空売り比率**: {format_percentage(supply_demand.short_selling_ratio, 2)}"

    def _format_technical_indicators(self, indicators: list[TechnicalIndicator]) -> str:
        """Format technical indicators table.

        Args:
            indicators: List of technical indicators.

        Returns:
            Formatted technical indicators table.
        """
        if not indicators:
            return "データがありません。"

        headers = ["指標", "値", "シグナル"]
        rows = []

        for ind in indicators:
            rows.append([ind.name, format_number(ind.value, 2), ind.signal])

        return create_markdown_table(headers, rows, alignments=["left", "right", "left"])

    def _generate_next_day_focus(
        self,
        market_summary: MarketSummary,
        sector_analysis: SectorAnalysis,
        technical_summary: TechnicalSummary,
    ) -> str:
        """Generate next day focus points.

        Args:
            market_summary: Market summary data.
            sector_analysis: Sector analysis data.
            technical_summary: Technical summary data.

        Returns:
            Next day focus points text.
        """
        focus_points = []

        # Market trend
        if market_summary.indices:
            main_index = market_summary.indices[0]
            if main_index.change_pct > 1.0:
                focus_points.append("- 主要指数が大幅高となった流れを継続できるか注目")
            elif main_index.change_pct < -1.0:
                focus_points.append("- 主要指数の下落からの反発力に注目")
            else:
                focus_points.append("- 主要指数の方向感に注目")

        # Sector focus
        if sector_analysis.sectors:
            top_sector = max(sector_analysis.sectors, key=lambda s: s.change_pct)
            focus_points.append(f"- {top_sector.name}セクターの続伸に注目")

        # Market breadth
        total = market_summary.advancing + market_summary.declining + market_summary.unchanged
        adv_ratio = (market_summary.advancing / total) if total > 0 else 0
        if adv_ratio > 0.7:
            focus_points.append("- 市場全体の強さが継続するか注目")
        elif adv_ratio < 0.3:
            focus_points.append("- 市場センチメントの改善に注目")

        # Default point
        if not focus_points:
            focus_points.append("- 市場全体の動向に注目")

        return "\n".join(focus_points)

    def _generate_market_comment(self, market_summary: MarketSummary) -> str:
        """Generate market overview comment based on data.

        Args:
            market_summary: Market summary data.

        Returns:
            Market commentary string.
        """
        comments = []

        # Analyze main index movement
        if market_summary.indices:
            main_index = market_summary.indices[0]
            if main_index.change_pct > 2.0:
                comments.append(f"{main_index.name}は大幅高となり、{main_index.change_pct:.2f}%上昇しました")
            elif main_index.change_pct > 1.0:
                comments.append(f"{main_index.name}は堅調に推移し、{main_index.change_pct:.2f}%上昇しました")
            elif main_index.change_pct > 0:
                comments.append(f"{main_index.name}は小幅高で、{main_index.change_pct:.2f}%上昇しました")
            elif main_index.change_pct > -1.0:
                comments.append(f"{main_index.name}は小幅安で、{main_index.change_pct:.2f}%下落しました")
            elif main_index.change_pct > -2.0:
                comments.append(f"{main_index.name}は軟調に推移し、{main_index.change_pct:.2f}%下落しました")
            else:
                comments.append(f"{main_index.name}は大幅安となり、{main_index.change_pct:.2f}%下落しました")

        # Analyze market breadth
        total = market_summary.advancing + market_summary.declining + market_summary.unchanged
        if total > 0:
            adv_ratio = market_summary.advancing / total
            if adv_ratio > 0.7:
                comments.append("値上がり銘柄が全体の7割を超え、全面高の展開となりました")
            elif adv_ratio > 0.6:
                comments.append("値上がり銘柄が優勢で、買い優勢の展開となりました")
            elif adv_ratio < 0.3:
                comments.append("値下がり銘柄が全体の7割を超え、全面安の展開となりました")
            elif adv_ratio < 0.4:
                comments.append("値下がり銘柄が優勢で、売り優勢の展開となりました")
            else:
                comments.append("値上がり・値下がり銘柄数が拮抗し、方向感に欠ける展開となりました")

        # Analyze trading volume
        if market_summary.total_turnover > 0:
            turnover_trillion = market_summary.total_turnover / 1_000_000_000_000
            if turnover_trillion > 4.0:
                comments.append(f"売買代金は{turnover_trillion:.1f}兆円と活況でした")
            elif turnover_trillion > 3.0:
                comments.append(f"売買代金は{turnover_trillion:.1f}兆円と堅調でした")
            elif turnover_trillion < 2.0:
                comments.append(f"売買代金は{turnover_trillion:.1f}兆円と低調でした")

        if not comments:
            return "本日の市場動向について特記事項はありません。"

        return "。".join(comments) + "。"

    def _generate_sector_comment(self, sector_analysis: SectorAnalysis) -> str:
        """Generate sector analysis comment based on data.

        Args:
            sector_analysis: Sector analysis data.

        Returns:
            Sector commentary string.
        """
        if not sector_analysis.sectors:
            return "セクター動向について特記事項はありません。"

        comments = []

        # Sort sectors by change percentage
        sorted_sectors = sorted(sector_analysis.sectors, key=lambda s: s.change_pct, reverse=True)

        # Top performers
        top_sectors = [s for s in sorted_sectors[:3] if s.change_pct > 0.5]
        if top_sectors:
            names = "、".join([s.name for s in top_sectors])
            comments.append(f"{names}が上昇率上位となりました")

        # Bottom performers
        bottom_sectors = [s for s in sorted_sectors[-3:] if s.change_pct < -0.5]
        if bottom_sectors:
            names = "、".join([s.name for s in bottom_sectors])
            comments.append(f"{names}が下落しました")

        # Strong sector movement
        strong_up = [s for s in sorted_sectors if s.change_pct > 2.0]
        if strong_up:
            for s in strong_up[:2]:
                comments.append(f"{s.name}は{s.change_pct:.2f}%と大幅高")

        strong_down = [s for s in sorted_sectors if s.change_pct < -2.0]
        if strong_down:
            for s in strong_down[:2]:
                comments.append(f"{s.name}は{abs(s.change_pct):.2f}%と大幅安")

        if not comments:
            return "セクター動向について特記事項はありません。"

        return "。".join(comments) + "。"

    def _generate_supply_demand_comment(self, supply_demand: SupplyDemandSummary) -> str:
        """Generate supply/demand comment based on data.

        Args:
            supply_demand: Supply and demand summary data.

        Returns:
            Supply/demand commentary string.
        """
        comments = []

        # Margin trading analysis
        if supply_demand.margin_buying_balance > 0 or supply_demand.margin_selling_balance > 0:
            if supply_demand.margin_ratio > 0:
                if supply_demand.margin_ratio > 3.0:
                    comments.append(f"信用倍率は{supply_demand.margin_ratio:.2f}倍と買い残が優勢で、需給面での重しとなる可能性があります")
                elif supply_demand.margin_ratio > 2.0:
                    comments.append(f"信用倍率は{supply_demand.margin_ratio:.2f}倍とやや買い残が多い状況です")
                elif supply_demand.margin_ratio < 1.0:
                    comments.append(f"信用倍率は{supply_demand.margin_ratio:.2f}倍と売り残が優勢で、踏み上げの可能性があります")
                else:
                    comments.append(f"信用倍率は{supply_demand.margin_ratio:.2f}倍と均衡した水準です")

        # Short selling analysis
        if supply_demand.short_selling_ratio > 0:
            if supply_demand.short_selling_ratio > 45:
                comments.append(f"空売り比率は{supply_demand.short_selling_ratio:.1f}%と高水準で、短期的な買い戻しが入りやすい状況です")
            elif supply_demand.short_selling_ratio > 40:
                comments.append(f"空売り比率は{supply_demand.short_selling_ratio:.1f}%とやや高めの水準です")
            elif supply_demand.short_selling_ratio < 35:
                comments.append(f"空売り比率は{supply_demand.short_selling_ratio:.1f}%と低めの水準です")
            else:
                comments.append(f"空売り比率は{supply_demand.short_selling_ratio:.1f}%と通常の水準です")

        if not comments:
            return "需給動向について特記事項はありません。"

        return "。".join(comments) + "。"

    def _generate_technical_comment(self, technical_summary: TechnicalSummary) -> str:
        """Generate technical analysis comment based on data.

        Args:
            technical_summary: Technical summary data.

        Returns:
            Technical commentary string.
        """
        comments = []

        # Moving average analysis
        for ma in technical_summary.moving_averages:
            if "25日" in ma.name:
                if ma.value > 70:
                    comments.append(f"25日移動平均線を上回る銘柄が{ma.value:.1f}%と多く、短期的に強い相場です")
                elif ma.value < 30:
                    comments.append(f"25日移動平均線を上回る銘柄が{ma.value:.1f}%と少なく、短期的に弱い相場です")
            elif "75日" in ma.name:
                if ma.value > 70:
                    comments.append(f"75日移動平均線を上回る銘柄が{ma.value:.1f}%と多く、中期的に強い相場です")
                elif ma.value < 30:
                    comments.append(f"75日移動平均線を上回る銘柄が{ma.value:.1f}%と少なく、中期的に弱い相場です")

        # Momentum analysis
        for momentum in technical_summary.momentum_indicators:
            if "騰落レシオ" in momentum.name:
                if momentum.value > 120:
                    comments.append(f"騰落レシオは{momentum.value:.1f}%と過熱感があり、短期的な調整に注意が必要です")
                elif momentum.value > 100:
                    comments.append(f"騰落レシオは{momentum.value:.1f}%と堅調な水準です")
                elif momentum.value < 80:
                    comments.append(f"騰落レシオは{momentum.value:.1f}%と売られ過ぎの水準で、反発が期待できます")
                elif momentum.value < 100:
                    comments.append(f"騰落レシオは{momentum.value:.1f}%とやや弱含みの水準です")

        if not comments:
            return "テクニカル指標について特記事項はありません。"

        return "。".join(comments) + "。"
