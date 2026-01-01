# データ処理モジュール - 実装ドキュメント

## 概要

J-Quants APIから取得したデータの処理・キャッシュシステム。効率的なデータ取得、正規化、永続化を提供します。

## アーキテクチャ

```
┌─────────────────┐
│  DataFetcher    │  API呼び出し + キャッシュ管理
└────────┬────────┘
         │
         ├─────────┐
         │         │
┌────────▼──────┐  │
│ CacheManager  │  │  Parquet形式でのローカルキャッシュ
└───────────────┘  │
         │         │
┌────────▼─────────▼──┐
│  DataProcessor      │  データ正規化・変換・統計
└─────────────────────┘
```

## モジュール構成

### 1. CacheManager (`cache.py`)

ローカルキャッシュの管理を担当。

#### 主な機能

- **Parquet形式でのキャッシュ**: 高速・省メモリ
- **自動有効期限管理**: TTL（Time-To-Live）ベース
- **差分更新対応**: キャッシュの選択的無効化
- **容量管理**: キャッシュサイズの追跡

#### 使用例

```python
from pathlib import Path
from jquants_report.data.cache import CacheManager

# 初期化
cache = CacheManager(
    cache_dir=Path("./data/cache"),
    default_ttl_hours=24
)

# データの保存
cache.set("daily_quotes_20240115", df, ttl_hours=24)

# データの取得
cached_df = cache.get("daily_quotes_20240115")

# キャッシュの無効化
cache.invalidate("daily_quotes_20240115")

# 期限切れキャッシュのクリーンアップ
cache.cleanup_expired()

# 全キャッシュのクリア
cache.clear_all()
```

#### API リファレンス

| メソッド | 説明 | パラメータ | 戻り値 |
|---------|------|----------|--------|
| `get(key)` | キャッシュからデータ取得 | `key: str` | `Optional[pd.DataFrame]` |
| `set(key, data, ttl_hours)` | データをキャッシュ | `key: str`<br>`data: pd.DataFrame`<br>`ttl_hours: Optional[int]` | `None` |
| `invalidate(key)` | 特定キャッシュを無効化 | `key: str` | `None` |
| `clear_all()` | 全キャッシュをクリア | - | `None` |
| `cleanup_expired()` | 期限切れを削除 | - | `int` (削除数) |
| `get_cache_size()` | キャッシュサイズ取得 | - | `int` (バイト) |

### 2. DataFetcher (`fetcher.py`)

J-Quants APIからのデータ取得を担当。

#### 主な機能

- **レート制限**: 1秒間隔でAPI呼び出し
- **自動キャッシュ**: 同一リクエストの重複回避
- **エラーハンドリング**: APIエラー時の安全な処理
- **日付範囲取得**: 複数日のデータを一括取得

#### 使用例

```python
from datetime import date
from jquants_report.data.fetcher import DataFetcher

# 初期化（APIクライアントとキャッシュマネージャーが必要）
fetcher = DataFetcher(api_client, cache_manager)

# 銘柄情報の取得
listed_info = fetcher.fetch_listed_info()

# 日次株価の取得
target_date = date(2024, 1, 15)
daily_quotes = fetcher.fetch_daily_quotes(target_date)

# 特定銘柄の株価取得
quotes_1301 = fetcher.fetch_daily_quotes(target_date, code="1301")

# 指数データの取得
indices = fetcher.fetch_indices(target_date)

# 投資部門別売買状況
trades_spec = fetcher.fetch_trades_spec(target_date)

# 信用取引残高
margin = fetcher.fetch_margin_interest(target_date)

# 空売り比率
short_selling = fetcher.fetch_short_selling(target_date)

# 財務諸表
statements = fetcher.fetch_statements("1301")

# 決算発表予定
announcements = fetcher.fetch_announcement()

# 日付範囲での取得
from datetime import timedelta
start_date = date(2024, 1, 15)
end_date = start_date + timedelta(days=7)
range_quotes = fetcher.fetch_date_range_quotes(start_date, end_date)

# キャッシュを無視して強制取得
fresh_data = fetcher.fetch_daily_quotes(target_date, force_refresh=True)
```

#### API リファレンス

| メソッド | 説明 | キャッシュTTL |
|---------|------|-------------|
| `fetch_listed_info()` | 銘柄マスタ | 24時間 |
| `fetch_daily_quotes(date, code)` | 日次株価 | 24時間 |
| `fetch_indices(date)` | 指数データ | 24時間 |
| `fetch_topix(date)` | TOPIX | 24時間 |
| `fetch_trades_spec(date)` | 投資部門別 | 24時間 |
| `fetch_margin_interest(date)` | 信用残高 | 24時間 |
| `fetch_short_selling(date)` | 空売り比率 | 24時間 |
| `fetch_statements(code)` | 財務諸表 | 24時間 |
| `fetch_announcement()` | 決算予定 | 6時間 |
| `fetch_date_range_quotes(start, end)` | 期間株価 | - |

### 3. DataProcessor (`processor.py`)

データの正規化・変換・分析を担当。

#### 主な機能

- **カラム名の標準化**: 一貫性のある命名規則
- **型変換**: 文字列→数値、日付変換
- **データクレンジング**: 欠損値・異常値の処理
- **派生カラムの追加**: 変化率などの計算
- **統計計算**: 基本統計量の算出
- **データ結合**: マスタデータとの結合

#### 使用例

```python
from jquants_report.data.processor import DataProcessor

processor = DataProcessor()

# 日次株価の処理
processed_quotes = processor.process_daily_quotes(raw_quotes)
# 追加される派生カラム: price_change, price_change_pct

# 銘柄情報の処理
processed_info = processor.process_listed_info(raw_info)

# 指数データの処理
processed_indices = processor.process_indices(raw_indices)
# 追加される派生カラム: change, change_pct

# 投資部門別の処理
processed_trades = processor.process_trades_spec(raw_trades)

# 信用残高の処理
processed_margin = processor.process_margin_interest(raw_margin)

# 空売り比率の処理
processed_short = processor.process_short_selling(raw_short)

# 財務諸表の処理
processed_statements = processor.process_statements(raw_statements)

# 決算予定の処理
processed_announcements = processor.process_announcement(raw_announcements)

# 統計計算
stats = processor.calculate_statistics(
    processed_quotes,
    value_column="close",
    group_by="code"  # オプション: グループ化
)

# マスタデータとの結合
enriched = processor.merge_with_master(
    processed_quotes,
    processed_info,
    on="code"
)

# 日付範囲でのフィルタ
from datetime import datetime
filtered = processor.filter_by_date_range(
    processed_quotes,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    date_column="date"
)

# 銘柄コードでのフィルタ
selected = processor.filter_by_codes(
    processed_quotes,
    codes=["1301", "1302", "1303"],
    code_column="code"
)
```

#### 処理済みデータのカラム構成

##### 日次株価 (process_daily_quotes)

| カラム名 | 型 | 説明 |
|---------|---|------|
| code | str | 銘柄コード |
| date | datetime | 日付 |
| open | float | 始値 |
| high | float | 高値 |
| low | float | 安値 |
| close | float | 終値 |
| volume | float | 出来高 |
| price_change | float | 値幅（終値-始値）|
| price_change_pct | float | 変化率（%） |

##### 銘柄マスタ (process_listed_info)

| カラム名 | 型 | 説明 |
|---------|---|------|
| code | str | 銘柄コード |
| company_name | str | 会社名 |
| sector_17_code | str | 17業種コード |
| sector_17_name | str | 17業種名 |
| sector_33_code | str | 33業種コード |
| sector_33_name | str | 33業種名 |
| market_code | str | 市場コード |
| market_name | str | 市場名 |

## 統合例

### 完全なワークフロー

```python
from datetime import date, timedelta
from pathlib import Path
from jquants_report.config import load_config
from jquants_report.api.client import JQuantsClient
from jquants_report.data import CacheManager, DataFetcher, DataProcessor

# 設定の読み込み
config = load_config()

# コンポーネントの初期化
api_client = JQuantsClient(config.jquants)
cache_manager = CacheManager(config.app.cache_dir)
fetcher = DataFetcher(api_client, cache_manager)
processor = DataProcessor()

# データ取得と処理
target_date = date.today() - timedelta(days=1)

# 1. 生データの取得
print("Fetching data...")
daily_quotes = fetcher.fetch_daily_quotes(target_date)
listed_info = fetcher.fetch_listed_info()
indices = fetcher.fetch_indices(target_date)

# 2. データ処理
print("Processing data...")
processed_quotes = processor.process_daily_quotes(daily_quotes)
processed_info = processor.process_listed_info(listed_info)
processed_indices = processor.process_indices(indices)

# 3. データ結合
print("Merging data...")
enriched_quotes = processor.merge_with_master(
    processed_quotes,
    processed_info,
    on="code"
)

# 4. 分析
print("Analyzing...")
# 業種別統計
sector_stats = processor.calculate_statistics(
    enriched_quotes,
    value_column="close",
    group_by="sector_17_name"
)

# トップパフォーマー
top_gainers = enriched_quotes.nlargest(10, "price_change_pct")

# 出来高上位
high_volume = enriched_quotes.nlargest(10, "volume")

print("Analysis complete!")
```

## パフォーマンス最適化

### キャッシュ戦略

1. **階層的キャッシュ**
   - マスタデータ: 24時間
   - 日次データ: 24時間
   - 決算予定: 6時間

2. **メモリ効率**
   - Parquet形式で圧縮保存
   - 必要なカラムのみ読み込み

3. **差分更新**
   ```python
   # 新しいデータのみ取得
   if cache.get(f"quotes_{date}") is None:
       new_data = fetcher.fetch_daily_quotes(date)
   ```

### レート制限対応

DataFetcherは自動的に1秒間隔を維持します。

```python
# 連続呼び出しでも安全
for i in range(10):
    data = fetcher.fetch_daily_quotes(date(2024, 1, i+1))
    # 自動的にレート制限が適用される
```

## エラーハンドリング

### 基本方針

- API呼び出しエラー: 空DataFrameを返す
- データ処理エラー: ログ出力 + 部分的な処理継続
- キャッシュエラー: 警告ログ + キャッシュなしで継続

### 例

```python
import logging

logging.basicConfig(level=logging.INFO)

# エラーが発生しても続行
data = fetcher.fetch_daily_quotes(target_date)
if data.empty:
    print("No data available, using cached data")
    # フォールバック処理
```

## テスト

### テスト実行

```bash
# 全テスト
uv run pytest tests/test_cache.py tests/test_data_processor.py tests/test_data_fetcher.py -v

# カバレッジ付き
uv run pytest tests/ --cov=src/jquants_report/data --cov-report=html

# 特定テスト
uv run pytest tests/test_cache.py::TestCacheManager::test_cache_expiration -v
```

### テストカバレッジ

- `test_cache.py`: CacheManagerの全機能
- `test_data_processor.py`: DataProcessorの全機能
- `test_data_fetcher.py`: DataFetcherの全機能（モックAPI使用）

## トラブルシューティング

### よくある問題

#### 1. キャッシュが期待通りに機能しない

```python
# デバッグログを有効化
import logging
logging.basicConfig(level=logging.DEBUG)

# キャッシュ状態を確認
cache_size = cache_manager.get_cache_size()
print(f"Cache size: {cache_size} bytes")

# 期限切れをクリーンアップ
removed = cache_manager.cleanup_expired()
print(f"Removed {removed} expired entries")
```

#### 2. API呼び出しが遅い

```python
# force_refreshを使用していないか確認
data = fetcher.fetch_daily_quotes(date, force_refresh=False)

# レート制限を確認
# MIN_REQUEST_INTERVAL = 1.0秒は変更不可
```

#### 3. メモリ使用量が多い

```python
# 必要なカラムのみ選択
processed = processor.process_daily_quotes(raw_data)
selected = processed[["code", "date", "close", "volume"]]

# 不要なキャッシュを削除
cache_manager.cleanup_expired()
```

## ベストプラクティス

### 1. 定期的なキャッシュクリーンアップ

```python
# 毎日のバッチ処理の最後に
cache_manager.cleanup_expired()
```

### 2. エラーログの監視

```python
import logging
logger = logging.getLogger("jquants_report.data")
logger.setLevel(logging.INFO)
```

### 3. データ検証

```python
# 処理後のデータを検証
if processed_data.empty:
    logger.warning("No data after processing")
else:
    logger.info(f"Processed {len(processed_data)} records")
```

## 今後の拡張

### 計画中の機能

- [ ] Redis/Memcachedサポート
- [ ] 非同期API呼び出し
- [ ] データ検証ルール
- [ ] 自動リトライメカニズム
- [ ] キャッシュウォームアップ

## 参考資料

- [J-Quants APIドキュメント](https://jpx.gitbook.io/j-quants-ja)
- [Pandas公式ドキュメント](https://pandas.pydata.org/docs/)
- [Parquetフォーマット](https://parquet.apache.org/)
