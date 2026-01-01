"""Tests for report generation module."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from jquants_report.report.formatter import (
    create_markdown_table,
    format_amount,
    format_change,
    format_date,
    format_number,
    format_percentage,
    format_strength_indicator,
    format_table_row,
    format_table_separator,
    format_trend_indicator,
    format_volume,
)
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


class TestFormatter:
    """Test formatter functions."""

    def test_format_number(self) -> None:
        """Test number formatting."""
        assert format_number(1234567) == "1,234,567"
        assert format_number(1234.567, 2) == "1,234.57"
        assert format_number(None) == "N/A"
        assert format_number(0) == "0"

    def test_format_percentage(self) -> None:
        """Test percentage formatting."""
        assert format_percentage(1.5) == "+1.50%"
        assert format_percentage(-2.3, 1) == "-2.3%"
        assert format_percentage(0) == "+0.00%"
        assert format_percentage(None) == "N/A"

    def test_format_change(self) -> None:
        """Test change formatting."""
        assert format_change(123.45) == "+123.45"
        assert format_change(-67.89, 1) == "-67.9"
        assert format_change(0) == "+0.00"
        assert format_change(None) == "N/A"

    def test_format_date(self) -> None:
        """Test date formatting."""
        test_date = date(2024, 1, 15)
        assert format_date(test_date) == "2024年01月15日"

    def test_format_volume(self) -> None:
        """Test volume formatting."""
        assert format_volume(1234567) == "123.5万株"
        assert format_volume(123456789) == "1.2億株"
        assert format_volume(None) == "N/A"

    def test_format_amount(self) -> None:
        """Test amount formatting."""
        assert format_amount(12345678) == "1,234.6万円"
        assert format_amount(1234567890) == "12.3億円"
        assert format_amount(1234567890123) == "1.2兆円"
        assert format_amount(None) == "N/A"

    def test_format_table_row(self) -> None:
        """Test table row formatting."""
        values = ["Code", "Name", "Change"]
        result = format_table_row(values)
        assert result == "| Code | Name | Change |"

        widths = [6, 20, 8]
        result = format_table_row(values, widths)
        assert "Code" in result
        assert "Name" in result
        assert "Change" in result

    def test_format_table_separator(self) -> None:
        """Test table separator formatting."""
        widths = [6, 20, 8]
        result = format_table_separator(widths)
        assert result.startswith("|")
        assert result.endswith("|")
        assert "--------" in result

    def test_create_markdown_table(self) -> None:
        """Test markdown table creation."""
        headers = ["Code", "Name", "Change"]
        rows = [["1234", "Company A", "+5.2%"], ["5678", "Company B", "-3.1%"]]
        result = create_markdown_table(headers, rows)

        assert "Code" in result
        assert "Name" in result
        assert "Company A" in result
        assert "1234" in result
        assert "+5.2%" in result

        # Test empty rows
        assert create_markdown_table(headers, []) == ""

    def test_create_markdown_table_with_alignment(self) -> None:
        """Test markdown table with alignment."""
        headers = ["Left", "Center", "Right"]
        rows = [["A", "B", "C"]]
        result = create_markdown_table(headers, rows, alignments=["left", "center", "right"])

        assert "Left" in result
        assert ":" in result  # Alignment markers

    def test_format_trend_indicator(self) -> None:
        """Test trend indicator formatting."""
        assert format_trend_indicator(5.2) == "↑"
        assert format_trend_indicator(-3.1) == "↓"
        assert format_trend_indicator(0) == "→"
        assert format_trend_indicator(None) == "-"

    def test_format_strength_indicator(self) -> None:
        """Test strength indicator formatting."""
        assert format_strength_indicator(80) == "強い"
        assert format_strength_indicator(20) == "弱い"
        assert format_strength_indicator(50) == "中立"
        assert format_strength_indicator(None) == "N/A"

        # Custom thresholds
        assert format_strength_indicator(80, (40, 60)) == "強い"
        assert format_strength_indicator(20, (40, 60)) == "弱い"


class TestReportGenerator:
    """Test report generator."""

    @pytest.fixture
    def output_dir(self) -> Path:
        """Create temporary output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def market_summary(self) -> MarketSummary:
        """Create sample market summary."""
        return MarketSummary(
            indices=[
                IndexData(
                    name="日経平均",
                    close=30000.0,
                    change=200.0,
                    change_pct=0.67,
                    volume=1000000000,
                ),
                IndexData(
                    name="TOPIX",
                    close=2100.0,
                    change=10.0,
                    change_pct=0.48,
                    volume=800000000,
                ),
            ],
            advancing=1500,
            declining=800,
            unchanged=200,
            total_volume=2000000000,
            total_turnover=3000000000000,
            comment="市場は堅調に推移しました。",
        )

    @pytest.fixture
    def sector_analysis(self) -> SectorAnalysis:
        """Create sample sector analysis."""
        return SectorAnalysis(
            sectors=[
                SectorData(name="電気機器", change_pct=1.5, turnover=500000000000),
                SectorData(name="情報・通信", change_pct=1.2, turnover=450000000000),
                SectorData(name="輸送用機器", change_pct=-0.5, turnover=300000000000),
            ],
            comment="電気機器セクターが上昇を牽引しました。",
        )

    @pytest.fixture
    def stock_highlights(self) -> StockHighlights:
        """Create sample stock highlights."""
        return StockHighlights(
            top_gainers=[
                StockData(
                    code="1234",
                    name="テスト株式会社",
                    close=1000.0,
                    change=100.0,
                    change_pct=11.11,
                    volume=1000000,
                    turnover=1000000000,
                ),
            ],
            top_losers=[
                StockData(
                    code="5678",
                    name="サンプル株式会社",
                    close=500.0,
                    change=-50.0,
                    change_pct=-9.09,
                    volume=500000,
                    turnover=250000000,
                ),
            ],
            top_volume=[
                StockData(
                    code="9999",
                    name="出来高株式会社",
                    close=2000.0,
                    change=50.0,
                    change_pct=2.56,
                    volume=10000000,
                    turnover=20000000000,
                ),
            ],
            top_turnover=[
                StockData(
                    code="8888",
                    name="売買代金株式会社",
                    close=3000.0,
                    change=-100.0,
                    change_pct=-3.23,
                    volume=8000000,
                    turnover=24000000000,
                ),
            ],
        )

    @pytest.fixture
    def technical_summary(self) -> TechnicalSummary:
        """Create sample technical summary."""
        return TechnicalSummary(
            moving_averages=[
                TechnicalIndicator(name="5日移動平均", value=29800.0, signal="上昇"),
                TechnicalIndicator(name="25日移動平均", value=29500.0, signal="上昇"),
            ],
            momentum_indicators=[
                TechnicalIndicator(name="RSI(14)", value=65.0, signal="中立"),
                TechnicalIndicator(name="MACD", value=50.0, signal="買い"),
            ],
            comment="短期的には上昇トレンドが継続しています。",
        )

    @pytest.fixture
    def supply_demand(self) -> SupplyDemandSummary:
        """Create sample supply demand summary."""
        return SupplyDemandSummary(
            margin_buying_balance=1500000000000,
            margin_selling_balance=500000000000,
            margin_ratio=25.5,
            short_selling_ratio=42.3,
            comment="信用買い残が増加傾向にあります。",
        )

    def test_report_generation(
        self,
        output_dir: Path,
        market_summary: MarketSummary,
        sector_analysis: SectorAnalysis,
        stock_highlights: StockHighlights,
        technical_summary: TechnicalSummary,
        supply_demand: SupplyDemandSummary,
    ) -> None:
        """Test complete report generation."""
        generator = ReportGenerator(output_dir)
        target_date = date(2024, 1, 15)

        report_path = generator.generate(
            target_date=target_date,
            market_summary=market_summary,
            sector_analysis=sector_analysis,
            stock_highlights=stock_highlights,
            technical_summary=technical_summary,
            supply_demand=supply_demand,
        )

        # Check file exists
        assert report_path.exists()
        assert report_path.name == "market_report_20240115.md"

        # Read and check content
        content = report_path.read_text(encoding="utf-8")

        # Check date
        assert "2024年01月15日" in content

        # Check market data
        assert "日経平均" in content
        assert "30,000" in content
        assert "+0.67%" in content

        # Check sector data
        assert "電気機器" in content
        assert "+1.50%" in content

        # Check stock highlights
        assert "テスト株式会社" in content
        assert "1234" in content

        # Check technical indicators
        assert "5日移動平均" in content
        assert "RSI" in content

        # Check supply demand
        assert "信用買い残" in content
        assert "空売り比率" in content

        # Check comments
        assert "市場は堅調に推移しました。" in content
        assert "電気機器セクターが上昇を牽引しました。" in content

    def test_output_directory_creation(self) -> None:
        """Test output directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "reports" / "2024"
            assert not output_dir.exists()

            generator = ReportGenerator(output_dir)
            assert output_dir.exists()

    def test_format_market_overview(
        self, output_dir: Path, market_summary: MarketSummary
    ) -> None:
        """Test market overview formatting."""
        generator = ReportGenerator(output_dir)
        result = generator._format_market_overview(market_summary)

        assert "日経平均" in result
        assert "30,000" in result
        assert "TOPIX" in result

    def test_format_market_breadth(
        self, output_dir: Path, market_summary: MarketSummary
    ) -> None:
        """Test market breadth formatting."""
        generator = ReportGenerator(output_dir)
        result = generator._format_market_breadth(market_summary)

        assert "値上がり" in result
        assert "値下がり" in result
        assert "1,500" in result
        assert "800" in result

    def test_format_sector_performance(
        self, output_dir: Path, sector_analysis: SectorAnalysis
    ) -> None:
        """Test sector performance formatting."""
        generator = ReportGenerator(output_dir)
        result = generator._format_sector_performance(sector_analysis)

        assert "電気機器" in result
        assert "情報・通信" in result
        assert "+1.50%" in result

    def test_format_stock_table(self, output_dir: Path, stock_highlights: StockHighlights) -> None:
        """Test stock table formatting."""
        generator = ReportGenerator(output_dir)
        result = generator._format_stock_table(stock_highlights.top_gainers)

        assert "テスト株式会社" in result
        assert "1234" in result
        assert "1,000" in result

        # Test empty list
        result_empty = generator._format_stock_table([])
        assert "データがありません" in result_empty

    def test_format_technical_indicators(
        self, output_dir: Path, technical_summary: TechnicalSummary
    ) -> None:
        """Test technical indicators formatting."""
        generator = ReportGenerator(output_dir)
        result = generator._format_technical_indicators(technical_summary.moving_averages)

        assert "5日移動平均" in result
        assert "29,800" in result
        assert "上昇" in result

    def test_generate_next_day_focus(
        self,
        output_dir: Path,
        market_summary: MarketSummary,
        sector_analysis: SectorAnalysis,
        technical_summary: TechnicalSummary,
    ) -> None:
        """Test next day focus generation."""
        generator = ReportGenerator(output_dir)
        result = generator._generate_next_day_focus(
            market_summary, sector_analysis, technical_summary
        )

        assert len(result) > 0
        assert "注目" in result

    def test_empty_data_handling(self, output_dir: Path) -> None:
        """Test handling of empty or minimal data."""
        generator = ReportGenerator(output_dir)

        # Empty market summary
        market_summary = MarketSummary(
            indices=[],
            advancing=0,
            declining=0,
            unchanged=0,
            total_volume=0,
            total_turnover=0,
        )

        sector_analysis = SectorAnalysis(sectors=[])
        stock_highlights = StockHighlights(
            top_gainers=[], top_losers=[], top_volume=[], top_turnover=[]
        )
        technical_summary = TechnicalSummary(moving_averages=[], momentum_indicators=[])
        supply_demand = SupplyDemandSummary(
            margin_buying_balance=0,
            margin_selling_balance=0,
            margin_ratio=0,
            short_selling_ratio=0,
        )

        target_date = date(2024, 1, 15)

        # Should not raise error
        report_path = generator.generate(
            target_date=target_date,
            market_summary=market_summary,
            sector_analysis=sector_analysis,
            stock_highlights=stock_highlights,
            technical_summary=technical_summary,
            supply_demand=supply_demand,
        )

        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert len(content) > 0
