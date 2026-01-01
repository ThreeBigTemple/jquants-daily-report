"""Tests for analysis modules."""

import numpy as np
import pandas as pd
import pytest

from jquants_report.analysis.market import MarketAnalyzer, MarketOverview
from jquants_report.analysis.sector import SectorAnalyzer, SectorPerformance
from jquants_report.analysis.stocks import StockAnalyzer, StockInfo
from jquants_report.analysis.supply_demand import (
    InvestorTradingSummary,
    MarginTradingSummary,
    SupplyDemandAnalyzer,
    SupplyDemandAnalysis,
)
from jquants_report.analysis.technical import TechnicalAnalyzer, TechnicalIndicators


class TestMarketAnalyzer:
    """Tests for MarketAnalyzer."""

    @pytest.fixture
    def sample_prices_df(self) -> pd.DataFrame:
        """Create sample price data."""
        return pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003", "1004", "1005"],
                "CompanyName": ["Stock A", "Stock B", "Stock C", "Stock D", "Stock E"],
                "Close": [1000, 2000, 1500, 800, 1200],
                "ChangeRate": [2.5, -1.5, 0.0, 3.0, -2.0],
                "Volume": [100000, 200000, 150000, 80000, 120000],
                "TurnoverValue": [100000000, 400000000, 225000000, 64000000, 144000000],
            }
        )

    @pytest.fixture
    def sample_indices_df(self) -> pd.DataFrame:
        """Create sample index data."""
        return pd.DataFrame(
            {
                "Code": ["0000", "0010"],
                "Close": [2500.5, 38000.25],
                "ChangeRate": [1.2, 0.8],
            }
        )

    def test_analyze_market_overview(
        self, sample_prices_df: pd.DataFrame, sample_indices_df: pd.DataFrame
    ) -> None:
        """Test market overview analysis."""
        analyzer = MarketAnalyzer()
        result = analyzer.analyze("2024-01-15", sample_prices_df, sample_indices_df)

        assert isinstance(result, MarketOverview)
        assert result.date == "2024-01-15"
        assert result.advancing_issues == 2
        assert result.declining_issues == 2
        assert result.unchanged_issues == 1
        assert result.total_issues == 5
        assert result.total_volume == 650000.0
        assert result.total_value == 933000000.0
        assert result.topix_close == 2500.5
        assert result.nikkei225_close == 38000.25

    def test_analyze_empty_dataframe(self) -> None:
        """Test analysis with empty dataframe."""
        analyzer = MarketAnalyzer()
        result = analyzer.analyze("2024-01-15", pd.DataFrame())

        assert result.advancing_issues == 0
        assert result.declining_issues == 0
        assert result.total_volume == 0.0

    def test_calculate_market_breadth(self, sample_prices_df: pd.DataFrame) -> None:
        """Test market breadth calculation."""
        analyzer = MarketAnalyzer()
        breadth = analyzer.calculate_market_breadth(sample_prices_df)

        assert breadth["advance_decline_ratio"] == 1.0  # 2 advancing / 2 declining
        assert breadth["advance_percentage"] == 40.0  # 2/5 * 100
        assert breadth["decline_percentage"] == 40.0  # 2/5 * 100


class TestSectorAnalyzer:
    """Tests for SectorAnalyzer."""

    @pytest.fixture
    def sample_sector_df(self) -> pd.DataFrame:
        """Create sample sector data."""
        return pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003", "2001", "2002"],
                "CompanyName": ["Stock A", "Stock B", "Stock C", "Stock D", "Stock E"],
                "Sector33Code": ["3200", "3200", "3250", "6050", "6050"],
                "Sector33CodeName": ["化学", "化学", "医薬品", "情報・通信業", "情報・通信業"],
                "Close": [1000, 2000, 1500, 800, 1200],
                "ChangeRate": [2.5, -1.5, 3.0, 1.0, -2.0],
                "Volume": [100000, 200000, 150000, 80000, 120000],
                "TurnoverValue": [100000000, 400000000, 225000000, 64000000, 144000000],
            }
        )

    def test_analyze_sectors(self, sample_sector_df: pd.DataFrame) -> None:
        """Test sector analysis."""
        analyzer = SectorAnalyzer()
        results = analyzer.analyze_sectors(sample_sector_df)

        assert len(results) == 3  # 3 unique sectors
        assert all(isinstance(r, SectorPerformance) for r in results)

        # Results should be sorted by change rate
        assert results[0].average_change_pct >= results[1].average_change_pct

    def test_get_top_sectors(self, sample_sector_df: pd.DataFrame) -> None:
        """Test getting top performing sectors."""
        analyzer = SectorAnalyzer()
        all_sectors = analyzer.analyze_sectors(sample_sector_df)
        top_sectors = analyzer.get_top_sectors(all_sectors, top_n=2)

        assert len(top_sectors) == 2
        assert top_sectors[0].average_change_pct >= top_sectors[1].average_change_pct

    def test_get_bottom_sectors(self, sample_sector_df: pd.DataFrame) -> None:
        """Test getting bottom performing sectors."""
        analyzer = SectorAnalyzer()
        all_sectors = analyzer.analyze_sectors(sample_sector_df)
        bottom_sectors = analyzer.get_bottom_sectors(all_sectors, bottom_n=2)

        assert len(bottom_sectors) == 2
        assert bottom_sectors[0].average_change_pct <= bottom_sectors[1].average_change_pct


class TestStockAnalyzer:
    """Tests for StockAnalyzer."""

    @pytest.fixture
    def sample_stocks_df(self) -> pd.DataFrame:
        """Create sample stock data."""
        return pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003", "1004", "1005"],
                "CompanyName": ["Stock A", "Stock B", "Stock C", "Stock D", "Stock E"],
                "Close": [1000, 2000, 1500, 800, 1200],
                "ChangeRate": [5.0, -4.0, 3.0, 2.0, -3.0],
                "Volume": [1000000, 500000, 800000, 300000, 600000],
                "TurnoverValue": [1000000000, 1000000000, 1200000000, 240000000, 720000000],
                "Sector33CodeName": ["化学", "医薬品", "情報・通信業", "小売業", "銀行業"],
            }
        )

    def test_get_top_gainers(self, sample_stocks_df: pd.DataFrame) -> None:
        """Test getting top gaining stocks."""
        analyzer = StockAnalyzer()
        gainers = analyzer.get_top_gainers(sample_stocks_df, top_n=3)

        assert len(gainers) == 3
        assert all(isinstance(s, StockInfo) for s in gainers)
        assert gainers[0].change_pct >= gainers[1].change_pct >= gainers[2].change_pct
        assert gainers[0].change_pct == 5.0

    def test_get_top_losers(self, sample_stocks_df: pd.DataFrame) -> None:
        """Test getting top losing stocks."""
        analyzer = StockAnalyzer()
        losers = analyzer.get_top_losers(sample_stocks_df, top_n=3)

        assert len(losers) == 2  # Only 2 losing stocks
        assert all(isinstance(s, StockInfo) for s in losers)
        assert losers[0].change_pct <= losers[1].change_pct
        assert losers[0].change_pct == -4.0

    def test_get_high_volume_stocks(self, sample_stocks_df: pd.DataFrame) -> None:
        """Test getting high volume stocks."""
        analyzer = StockAnalyzer()
        high_vol = analyzer.get_high_volume_stocks(sample_stocks_df, top_n=3)

        assert len(high_vol) == 3
        assert all(isinstance(s, StockInfo) for s in high_vol)
        assert high_vol[0].volume >= high_vol[1].volume

    def test_get_limit_hits(self) -> None:
        """Test getting limit hit stocks."""
        df = pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003"],
                "CompanyName": ["Stock A", "Stock B", "Stock C"],
                "Close": [1000, 2000, 1500],
                "ChangeRate": [10.0, -10.0, 5.0],
                "Volume": [1000000, 500000, 800000],
                "TurnoverValue": [1000000000, 1000000000, 1200000000],
                "HighLimit": [True, False, False],
                "LowLimit": [False, True, False],
            }
        )

        analyzer = StockAnalyzer()
        limits = analyzer.get_limit_hits(df)

        assert len(limits["upper_limit"]) == 1
        assert len(limits["lower_limit"]) == 1
        assert limits["upper_limit"][0].code == "1001"
        assert limits["lower_limit"][0].code == "1002"

    def test_empty_dataframe(self) -> None:
        """Test with empty dataframe."""
        analyzer = StockAnalyzer()
        gainers = analyzer.get_top_gainers(pd.DataFrame())

        assert len(gainers) == 0


class TestTechnicalAnalyzer:
    """Tests for TechnicalAnalyzer."""

    @pytest.fixture
    def sample_current_df(self) -> pd.DataFrame:
        """Create sample current price data."""
        return pd.DataFrame(
            {
                "Code": ["1001", "1002", "1003"],
                "CompanyName": ["Stock A", "Stock B", "Stock C"],
                "Date": ["2024-01-15", "2024-01-15", "2024-01-15"],
                "Close": [1000, 2000, 1500],
                "High": [1050, 2100, 1550],
                "Low": [950, 1900, 1450],
                "ChangeRate": [2.0, -1.0, 1.5],
                "Volume": [100000, 200000, 150000],
            }
        )

    @pytest.fixture
    def sample_historical_df(self) -> pd.DataFrame:
        """Create sample historical data."""
        dates = pd.date_range(start="2024-01-01", periods=30, freq="D")
        data = []

        for date in dates:
            for code in ["1001", "1002", "1003"]:
                data.append(
                    {
                        "Code": code,
                        "Date": date.strftime("%Y-%m-%d"),
                        "Close": 1000 + np.random.randint(-50, 50),
                        "High": 1050 + np.random.randint(-50, 50),
                        "Low": 950 + np.random.randint(-50, 50),
                        "ChangeRate": np.random.uniform(-3, 3),
                        "Volume": 100000 + np.random.randint(-10000, 10000),
                    }
                )

        return pd.DataFrame(data)

    def test_analyze_technical_indicators(
        self, sample_current_df: pd.DataFrame, sample_historical_df: pd.DataFrame
    ) -> None:
        """Test technical indicator analysis."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.analyze("2024-01-15", sample_current_df, sample_historical_df)

        assert isinstance(result, TechnicalIndicators)
        assert result.date == "2024-01-15"
        # Note: Values depend on random data, so just check types
        assert isinstance(result.advance_decline_ratio_25d, (float, type(None)))
        assert isinstance(result.new_highs, int)
        assert isinstance(result.new_lows, int)

    def test_analyze_without_historical(self, sample_current_df: pd.DataFrame) -> None:
        """Test analysis without historical data."""
        analyzer = TechnicalAnalyzer()
        result = analyzer.analyze("2024-01-15", sample_current_df)

        assert isinstance(result, TechnicalIndicators)
        assert result.advance_decline_ratio_25d is None
        assert result.new_highs == 0
        assert result.new_lows == 0

    def test_calculate_rsi(self, sample_historical_df: pd.DataFrame) -> None:
        """Test RSI calculation."""
        analyzer = TechnicalAnalyzer()
        rsi = analyzer.calculate_rsi(sample_historical_df, "1001", period=14)

        if rsi is not None:
            assert 0 <= rsi <= 100


class TestSupplyDemandAnalyzer:
    """Tests for SupplyDemandAnalyzer."""

    @pytest.fixture
    def sample_trading_df(self) -> pd.DataFrame:
        """Create sample trading data."""
        return pd.DataFrame(
            {
                "InvestorType": ["1", "2", "3", "4"],
                "BuyValue": [1000, 2000, 1500, 800],
                "SellValue": [1200, 1800, 1600, 700],
                "BuyVolume": [100000, 200000, 150000, 80000],
                "SellVolume": [120000, 180000, 160000, 70000],
            }
        )

    @pytest.fixture
    def sample_margin_df(self) -> pd.DataFrame:
        """Create sample margin trading data."""
        return pd.DataFrame(
            {
                "MarginBuyBalance": [1000000, 1500000],
                "MarginSellBalance": [800000, 1200000],
                "MarginBuyValue": [1000, 1500],
                "MarginSellValue": [800, 1200],
            }
        )

    def test_analyze_investor_trading(self, sample_trading_df: pd.DataFrame) -> None:
        """Test investor trading analysis."""
        analyzer = SupplyDemandAnalyzer()
        results = analyzer.analyze_investor_trading(sample_trading_df)

        assert len(results) == 4
        assert all(isinstance(r, InvestorTradingSummary) for r in results)

        # Check calculations
        individual = next(r for r in results if r.investor_type == "個人")
        assert individual.buy_value == 1000
        assert individual.sell_value == 1200
        assert individual.net_value == -200

    def test_analyze_margin_trading(self, sample_margin_df: pd.DataFrame) -> None:
        """Test margin trading analysis."""
        analyzer = SupplyDemandAnalyzer()
        result = analyzer.analyze_margin_trading("2024-01-15", sample_margin_df)

        assert isinstance(result, MarginTradingSummary)
        assert result.date == "2024-01-15"
        assert result.margin_buy_balance == 2500000
        assert result.margin_sell_balance == 2000000
        assert result.margin_ratio is not None
        assert result.margin_ratio == 1.25

    def test_analyze_full(
        self, sample_trading_df: pd.DataFrame, sample_margin_df: pd.DataFrame
    ) -> None:
        """Test full supply/demand analysis."""
        analyzer = SupplyDemandAnalyzer()
        result = analyzer.analyze("2024-01-15", sample_trading_df, sample_margin_df)

        assert isinstance(result, SupplyDemandAnalysis)
        assert result.date == "2024-01-15"
        assert len(result.investor_trading) == 4
        assert result.margin_trading is not None

    def test_get_top_net_buyers(self, sample_trading_df: pd.DataFrame) -> None:
        """Test getting top net buyers."""
        analyzer = SupplyDemandAnalyzer()
        all_summaries = analyzer.analyze_investor_trading(sample_trading_df)
        top_buyers = analyzer.get_top_net_buyers(all_summaries, top_n=2)

        assert len(top_buyers) == 2
        assert top_buyers[0].net_value >= top_buyers[1].net_value

    def test_get_top_net_sellers(self, sample_trading_df: pd.DataFrame) -> None:
        """Test getting top net sellers."""
        analyzer = SupplyDemandAnalyzer()
        all_summaries = analyzer.analyze_investor_trading(sample_trading_df)
        top_sellers = analyzer.get_top_net_sellers(all_summaries, top_n=2)

        assert len(top_sellers) == 2
        assert top_sellers[0].net_value <= top_sellers[1].net_value

    def test_empty_dataframes(self) -> None:
        """Test with empty dataframes."""
        analyzer = SupplyDemandAnalyzer()
        result = analyzer.analyze("2024-01-15", pd.DataFrame(), pd.DataFrame())

        assert len(result.investor_trading) == 0
        assert result.margin_trading is None
