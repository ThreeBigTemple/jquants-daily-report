# レポート生成モジュール

分析結果をMarkdown形式のレポートに変換するモジュールです。

## モジュール構成

### formatter.py
データフォーマッティングユーティリティ関数を提供します。

**主な機能:**
- `format_number()`: 数値を3桁カンマ区切りでフォーマット
- `format_percentage()`: パーセンテージを符号付きでフォーマット
- `format_change()`: 変化値を符号付きでフォーマット
- `format_date()`: 日付を日本語形式でフォーマット (YYYY年MM月DD日)
- `format_volume()`: 出来高を万株/億株単位でフォーマット
- `format_amount()`: 金額を万円/億円/兆円単位でフォーマット
- `create_markdown_table()`: Markdownテーブルを生成
- `format_trend_indicator()`: トレンド矢印を生成 (↑/↓/→)
- `format_strength_indicator()`: 強弱指標を生成 (強い/弱い/中立)

### templates.py
Jinja2テンプレートを提供します。

**主な機能:**
- メインレポートテンプレート定義
- カスタムフィルタの登録
- テンプレートレンダリング関数

### generator.py
レポート生成の中核クラスと分析データのdataclassを提供します。

**データクラス:**
- `IndexData`: 指数データ
- `MarketSummary`: 市場概況データ
- `SectorData`: セクターデータ
- `SectorAnalysis`: セクター分析データ
- `StockData`: 個別銘柄データ
- `StockHighlights`: 個別銘柄ハイライトデータ
- `TechnicalIndicator`: テクニカル指標データ
- `TechnicalSummary`: テクニカルサマリーデータ
- `SupplyDemandSummary`: 需給分析データ

**ReportGeneratorクラス:**
- `generate()`: メインのレポート生成メソッド
- 各セクションのフォーマッティングメソッド

## 使用例

```python
from datetime import date
from pathlib import Path
from jquants_report.report import (
    ReportGenerator,
    MarketSummary,
    IndexData,
    SectorAnalysis,
    SectorData,
    StockHighlights,
    StockData,
    TechnicalSummary,
    TechnicalIndicator,
    SupplyDemandSummary,
)

# データの準備
market_summary = MarketSummary(
    indices=[
        IndexData(
            name="日経平均株価",
            close=33500.50,
            change=250.75,
            change_pct=0.75,
            volume=1250000000,
        ),
    ],
    advancing=1680,
    declining=750,
    unchanged=185,
    total_volume=2500000000,
    total_turnover=3850000000000,
    comment="本日の市場動向...",
)

sector_analysis = SectorAnalysis(
    sectors=[
        SectorData(name="電気機器", change_pct=2.15, turnover=680000000000),
        # ... その他のセクター
    ],
    comment="セクター分析コメント...",
)

# StockHighlights, TechnicalSummary, SupplyDemandSummary も同様に準備

# レポート生成
output_dir = Path("./reports")
generator = ReportGenerator(output_dir)

report_path = generator.generate(
    target_date=date(2024, 3, 15),
    market_summary=market_summary,
    sector_analysis=sector_analysis,
    stock_highlights=stock_highlights,
    technical_summary=technical_summary,
    supply_demand=supply_demand,
)

print(f"レポート生成完了: {report_path}")
```

## 出力形式

### ファイル名
`market_report_YYYYMMDD.md`

例: `market_report_20240315.md`

### レポート構成

1. **市場全体の概況**
   - 主要指数（終値、前日比、騰落率、出来高）
   - 騰落銘柄数（値上がり/値下がり/変わらず）
   - 市場コメント

2. **セクター分析**
   - セクター別騰落率（降順）
   - セクター別売買代金（上位10セクター）
   - セクターコメント

3. **個別銘柄ハイライト**
   - 値上がり率上位
   - 値下がり率上位
   - 出来高上位
   - 売買代金上位

4. **需給分析**
   - 信用残高（買い残/売り残）
   - 空売り比率
   - 需給コメント

5. **テクニカル指標サマリー**
   - 移動平均線
   - モメンタム指標
   - テクニカルコメント

6. **翌営業日の注目点**
   - 自動生成される注目ポイント

## テスト

テストスイートは `tests/test_report.py` に含まれています。

```bash
# テスト実行
uv run pytest tests/test_report.py -v

# カバレッジ付きテスト
uv run pytest tests/test_report.py --cov=jquants_report.report
```

## 型ヒント

すべての関数とメソッドに型ヒントが完備されています。型チェックは以下のコマンドで実行できます。

```bash
uv run mypy src/jquants_report/report/
```

## コーディング規約

- **docstring**: Google形式
- **命名規則**: PascalCase (クラス), snake_case (関数/変数)
- **型ヒント**: すべての関数・メソッドに必須
- **フォーマット**: 数値は3桁カンマ区切り、パーセンテージは小数点以下2桁
- **文字コード**: UTF-8

## 注意事項

1. レポートはテキストベースのMarkdown形式です
2. 色やアイコンは使用せず、矢印記号（↑/↓/→）やテキストで表現します
3. 数値フォーマットは日本の慣習に従います（万株、億円など）
4. すべてのセクションは空データでも正常に動作するように実装されています
