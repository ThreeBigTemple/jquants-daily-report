"""Example script to demonstrate report generation."""

from datetime import date
from pathlib import Path

from src.jquants_report.report import (
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


def main() -> None:
    """Generate example report."""
    # Create sample data
    market_summary = MarketSummary(
        indices=[
            IndexData(
                name="日経平均株価",
                close=33500.50,
                change=250.75,
                change_pct=0.75,
                volume=1250000000,
            ),
            IndexData(
                name="TOPIX",
                close=2380.25,
                change=15.30,
                change_pct=0.65,
                volume=950000000,
            ),
        ],
        advancing=1680,
        declining=750,
        unchanged=185,
        total_volume=2500000000,
        total_turnover=3850000000000,
        comment="本日の東京株式市場は、米国株高を受けて買いが先行し、日経平均は堅調に推移しました。"
        "半導体関連を中心にハイテク株が買われ、相場を牽引する展開となりました。",
    )

    sector_analysis = SectorAnalysis(
        sectors=[
            SectorData(name="電気機器", change_pct=2.15, turnover=680000000000),
            SectorData(name="情報・通信", change_pct=1.85, turnover=520000000000),
            SectorData(name="医薬品", change_pct=1.20, turnover=380000000000),
            SectorData(name="化学", change_pct=0.95, turnover=290000000000),
            SectorData(name="機械", change_pct=0.75, turnover=250000000000),
            SectorData(name="小売業", change_pct=-0.35, turnover=220000000000),
            SectorData(name="銀行業", change_pct=-0.60, turnover=310000000000),
            SectorData(name="不動産業", change_pct=-0.85, turnover=180000000000),
        ],
        comment="電気機器、情報・通信セクターが大幅高となり、市場全体の上昇を牽引しました。"
        "一方、内需関連の小売業や金融セクターは軟調な展開となりました。",
    )

    stock_highlights = StockHighlights(
        top_gainers=[
            StockData(
                code="6920",
                name="レーザーテック",
                close=28500.0,
                change=3200.0,
                change_pct=12.64,
                volume=2850000,
                turnover=81225000000,
            ),
            StockData(
                code="6857",
                name="アドバンテスト",
                close=5250.0,
                change=580.0,
                change_pct=12.42,
                volume=8920000,
                turnover=46830000000,
            ),
            StockData(
                code="8035",
                name="東京エレクトロン",
                close=24800.0,
                change=2100.0,
                change_pct=9.25,
                volume=3450000,
                turnover=85560000000,
            ),
        ],
        top_losers=[
            StockData(
                code="9983",
                name="ファーストリテイリング",
                close=38500.0,
                change=-1850.0,
                change_pct=-4.59,
                volume=1250000,
                turnover=48125000000,
            ),
            StockData(
                code="9984",
                name="ソフトバンクグループ",
                close=5850.0,
                change=-250.0,
                change_pct=-4.10,
                volume=15800000,
                turnover=92430000000,
            ),
            StockData(
                code="8306",
                name="三菱UFJフィナンシャル・グループ",
                close=1180.0,
                change=-42.0,
                change_pct=-3.44,
                volume=28500000,
                turnover=33630000000,
            ),
        ],
        top_volume=[
            StockData(
                code="8306",
                name="三菱UFJフィナンシャル・グループ",
                close=1180.0,
                change=-42.0,
                change_pct=-3.44,
                volume=28500000,
                turnover=33630000000,
            ),
            StockData(
                code="9984",
                name="ソフトバンクグループ",
                close=5850.0,
                change=-250.0,
                change_pct=-4.10,
                volume=15800000,
                turnover=92430000000,
            ),
            StockData(
                code="7203",
                name="トヨタ自動車",
                close=2850.0,
                change=35.0,
                change_pct=1.24,
                volume=12500000,
                turnover=35625000000,
            ),
        ],
        top_turnover=[
            StockData(
                code="9984",
                name="ソフトバンクグループ",
                close=5850.0,
                change=-250.0,
                change_pct=-4.10,
                volume=15800000,
                turnover=92430000000,
            ),
            StockData(
                code="8035",
                name="東京エレクトロン",
                close=24800.0,
                change=2100.0,
                change_pct=9.25,
                volume=3450000,
                turnover=85560000000,
            ),
            StockData(
                code="6920",
                name="レーザーテック",
                close=28500.0,
                change=3200.0,
                change_pct=12.64,
                volume=2850000,
                turnover=81225000000,
            ),
        ],
    )

    technical_summary = TechnicalSummary(
        moving_averages=[
            TechnicalIndicator(name="5日移動平均", value=33250.0, signal="上昇トレンド"),
            TechnicalIndicator(name="25日移動平均", value=32800.0, signal="上昇トレンド"),
            TechnicalIndicator(name="75日移動平均", value=31500.0, signal="上昇トレンド"),
        ],
        momentum_indicators=[
            TechnicalIndicator(name="RSI(14日)", value=68.5, signal="やや過熱"),
            TechnicalIndicator(name="MACD", value=125.5, signal="買いシグナル継続"),
            TechnicalIndicator(name="ストキャスティクス", value=75.2, signal="過熱圏"),
        ],
        comment="短期・中期・長期の移動平均線が全て上向きで、上昇トレンドが継続しています。"
        "ただし、RSIやストキャスティクスは過熱圏に近づいており、短期的な調整の可能性に注意が必要です。",
    )

    supply_demand = SupplyDemandSummary(
        margin_buying_balance=4250000000000,
        margin_selling_balance=1180000000000,
        margin_ratio=32.5,
        short_selling_ratio=45.8,
        comment="信用買い残が前週比で増加しており、投資家心理の強気化が見られます。"
        "ただし、空売り比率も高水準を維持しており、需給面での過熱感には注意が必要です。",
    )

    # Generate report
    output_dir = Path("./reports")
    generator = ReportGenerator(output_dir)

    target_date = date(2024, 3, 15)
    report_path = generator.generate(
        target_date=target_date,
        market_summary=market_summary,
        sector_analysis=sector_analysis,
        stock_highlights=stock_highlights,
        technical_summary=technical_summary,
        supply_demand=supply_demand,
    )

    print(f"Sample report generated: {report_path}")
    print("\nReport preview:")
    print("=" * 80)
    with open(report_path, "r", encoding="utf-8") as f:
        print(f.read())


if __name__ == "__main__":
    main()
