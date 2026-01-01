# J-Quants Daily Report

J-Quants API（Standardプラン）を使用した日次・週次株式市場レポート自動生成システム

## 機能

### 日次レポート
- 主要指数（TOPIX、日経225）の日次サマリー
- 33業種別セクター分析（騰落率・売買代金）
- 値上がり/値下がり率上位銘柄
- 出来高・売買代金上位銘柄
- 信用取引残高・空売り比率分析
- テクニカル指標（移動平均線乖離率、騰落レシオ）

### 週次レポート
- 週間市場サマリー（指数の日次推移、騰落銘柄数）
- セクターローテーション分析（上位/下位セクター、前週比較）
- 週間パフォーマンスランキング（値上がり/値下がり/売買代金上位）
- 投資部門別売買動向（外国人、個人、機関投資家）
- 信用取引動向（買い残/売り残、信用倍率推移）
- テクニカル指標サマリー（騰落レシオ、移動平均線分析）
- 来週の決算・イベントカレンダー
- 週間トピックス（注目の値動き、セクターハイライト）
- 中期トレンド確認（1週間/1ヶ月/3ヶ月トレンド）

## 必要要件

- Python 3.11+
- uv（パッケージ管理）
- J-Quants API Standardプラン

## セットアップ

```bash
# リポジトリのクローン
git clone <repository-url>
cd jquants-daily-report

# 仮想環境作成と依存関係インストール
uv sync

# 環境変数の設定
cp .env.example .env
# .env を編集してJ-Quants認証情報を設定
```

## 環境変数

`.env` ファイルに以下を設定：

```
JQUANTS_EMAIL=your-email@example.com
JQUANTS_PASSWORD=your-password
JQUANTS_REFRESH_TOKEN=xxx  # 初回実行後に自動取得
REPORT_OUTPUT_DIR=./reports
CACHE_DIR=./data
LOG_LEVEL=INFO
```

## 使い方

### 日次レポート

```bash
# 本日のレポート生成
uv run python -m jquants_report

# 特定日のレポート生成
uv run python -m jquants_report --date 2025-12-15

# ドライラン（キャッシュのみ使用、API呼び出しなし）
uv run python -m jquants_report --dry-run

# 詳細ログ出力
LOG_LEVEL=DEBUG uv run python -m jquants_report
```

### 週次レポート

```bash
# 直近金曜日の週次レポート生成
uv run python -m jquants_report --weekly

# 特定週のレポート生成（週末日付を指定）
uv run python -m jquants_report --weekly --week-end 2025-12-20

# 週次レポートのドライラン
uv run python -m jquants_report --weekly --dry-run
```

## 出力例

### 日次レポート
レポートは `./reports/market_report_YYYYMMDD.md` として出力されます。

### 週次レポート
レポートは `./reports/weekly_report_YYYYMMDD.md`（週末日付）として出力されます。

```markdown
# 日次株式市場レポート - 2025年12月15日

## 1. 市場全体の概況

### 主要指数
| 指数    | 終値       | 前日比      | 騰落率    |
|:-----|--------:|--------:|------:|
| TOPIX | 2,746.56 | +4.44 ↑ | +0.16% |

### 騰落銘柄数
| 項目   | 銘柄数   | 比率    |
|:----|-----:|-----:|
| 値上がり | 1,892   | 49.3% |
| 値下がり | 1,789 | 46.6% |
...
```

## プロジェクト構造

```
jquants-daily-report/
├── src/jquants_report/
│   ├── main.py              # CLIエントリーポイント
│   ├── config.py            # 設定・環境変数管理
│   ├── api/                 # J-Quants APIクライアント
│   ├── data/                # データ取得・キャッシュ
│   │   ├── cache.py         # SQLiteキャッシュ管理
│   │   ├── fetcher.py       # データ取得
│   │   └── weekly_aggregator.py  # 週次データ集約
│   ├── analysis/            # 分析ロジック
│   │   ├── market.py        # 市場分析（日次）
│   │   ├── sector.py        # セクター分析（日次）
│   │   ├── stocks.py        # 個別銘柄分析（日次）
│   │   ├── technical.py     # テクニカル指標（日次）
│   │   ├── supply_demand.py # 需給分析（日次）
│   │   └── weekly/          # 週次分析モジュール
│   │       ├── market.py    # 週間市場サマリー
│   │       ├── sector.py    # セクターローテーション
│   │       ├── stocks.py    # パフォーマンスランキング
│   │       ├── investor.py  # 投資部門別売買動向
│   │       ├── margin.py    # 信用取引動向
│   │       ├── technical.py # テクニカルサマリー
│   │       ├── events.py    # 決算・イベントカレンダー
│   │       ├── topics.py    # 週間トピックス
│   │       └── trends.py    # 中期トレンド確認
│   └── report/              # レポート生成
│       ├── generator.py     # 日次レポート生成
│       ├── weekly_generator.py  # 週次レポート生成
│       └── weekly_types.py  # 週次レポート用データ型
├── data/                    # キャッシュデータ
│   └── cache.db             # SQLiteデータベース
├── reports/                 # 出力レポート
└── tests/                   # テスト
```

## データキャッシュ

APIから取得したデータはSQLiteデータベース（`./data/cache.db`）にキャッシュされます。

- デフォルトTTL: 24時間
- キャッシュ対象: 株価、指数、上場銘柄情報、信用残高など
- 旧形式（parquet/meta）からの自動マイグレーション対応

キャッシュの確認：
```bash
sqlite3 ./data/cache.db "SELECT cache_key, row_count, expires_at FROM cache_entries;"
```

## 開発

```bash
# テスト実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src/jquants_report

# リント・フォーマット
uv run ruff check src/
uv run ruff format src/

# 型チェック
uv run mypy src/
```

## ライセンス

MIT License
