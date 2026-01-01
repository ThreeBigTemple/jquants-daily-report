# J-Quants 日次株式市場レポートシステム開発プロンプト

## プロジェクト概要

J-Quants API（Standardプラン）を使用して、毎日株式市場がしまった後に本日の値動きなど株式市場の動向をMarkdown形式のレポートとして出力するPythonシステムを開発する。

## 技術要件

- **言語**: Python 3.11+
- **パッケージ管理・仮想環境**: uv（pipは使用しない）
- **出力形式**: Markdown（.md）
- **API**: J-Quants API Standardプラン

## レポート構成

### 1. 市場全体の概況
- 主要指数（日経225、TOPIX、グロース市場250）の終値・前日比・騰落率
- 市場全体の出来高・売買代金
- 騰落銘柄数（値上がり・値下がり・変わらず）

### 2. セクター分析
- 33業種別騰落率ランキング
- 業種別の強弱をヒートマップ的に表現（テキストベース）

### 3. 個別銘柄ハイライト
- 値上がり率TOP10 / 値下がり率TOP10
- 出来高急増銘柄（過去20日平均比で2倍以上）
- ストップ高・ストップ安銘柄
- 年初来高値・安値更新銘柄

### 4. 需給分析
- 投資部門別売買状況（外国人・個人・信託銀行など）
- 信用取引残高の推移、貸借倍率

### 5. テクニカル指標サマリー
- 騰落レシオ（25日）
- 25日移動平均線との乖離率分布
- 新高値・新安値銘柄数

### 6. 翌営業日の注目点
- 決算発表予定銘柄リスト
- 権利落ち・株式分割などのコーポレートアクション

## ディレクトリ構成

```
jquants-daily-report/
├── pyproject.toml          # uv プロジェクト設定
├── .python-version         # Python バージョン指定
├── CLAUDE.md               # Claude Code 用コンテキスト
├── .mcp.json               # MCP サーバー設定
├── .env                    # 環境変数（API認証情報）
├── .env.example            # 環境変数テンプレート
├── .gitignore
├── README.md
├── src/
│   └── jquants_report/
│       ├── __init__.py
│       ├── main.py              # エントリーポイント
│       ├── config.py            # 設定管理
│       ├── api/
│       │   ├── __init__.py
│       │   ├── client.py        # J-Quants APIクライアント
│       │   ├── auth.py          # 認証処理
│       │   └── endpoints.py     # エンドポイント定義
│       ├── data/
│       │   ├── __init__.py
│       │   ├── fetcher.py       # データ取得
│       │   ├── processor.py     # データ加工
│       │   └── cache.py         # キャッシュ管理
│       ├── analysis/
│       │   ├── __init__.py
│       │   ├── market.py        # 市場全体分析
│       │   ├── sector.py        # セクター分析
│       │   ├── stocks.py        # 個別銘柄分析
│       │   ├── technical.py     # テクニカル指標
│       │   └── supply_demand.py # 需給分析
│       └── report/
│           ├── __init__.py
│           ├── generator.py     # レポート生成
│           ├── templates.py     # Markdownテンプレート
│           └── formatter.py     # フォーマッター
├── reports/                     # 生成レポート出力先
│   └── .gitkeep
├── data/                        # キャッシュデータ
│   └── .gitkeep
└── tests/
    ├── __init__.py
    ├── test_api.py
    ├── test_analysis.py
    └── test_report.py
```

## 実装手順

### Phase 1: プロジェクトセットアップ
1. uvでプロジェクト初期化
2. 必要な依存関係を追加（pandas, requests, python-dotenv等）
3. ディレクトリ構造の作成
4. 環境変数の設定

### Phase 2: API クライアント実装
1. J-Quants API認証処理（リフレッシュトークン/IDトークン）
2. 各エンドポイントへのアクセス実装
3. レート制限対応
4. エラーハンドリング

### Phase 3: データ取得・加工
1. 株価データ取得
2. 財務データ取得
3. 投資部門別売買状況取得
4. 信用取引データ取得
5. データの正規化・キャッシュ

### Phase 4: 分析ロジック実装
1. 市場概況の算出
2. セクター分析
3. 個別銘柄スクリーニング
4. テクニカル指標計算
5. 需給分析

### Phase 5: レポート生成
1. Markdownテンプレート作成
2. 各セクションのレンダリング
3. 日付ベースのファイル出力

### Phase 6: テスト・最適化
1. ユニットテスト作成
2. 統合テスト
3. パフォーマンス最適化

## J-Quants API Standardプラン利用可能エンドポイント

```
# 認証
POST /token/auth_user      # リフレッシュトークン取得
POST /token/auth_refresh   # IDトークン取得

# 上場銘柄一覧
GET /listed/info           # 銘柄情報

# 株価
GET /prices/daily_quotes   # 日次株価（当日含む過去2年分）

# 財務情報
GET /fins/statements       # 財務諸表
GET /fins/announcement     # 決算発表日

# 指数
GET /indices               # 指数データ
GET /indices/topix         # TOPIX

# 投資部門別売買状況
GET /markets/trades_spec   # 投資部門別売買状況

# 信用取引
GET /markets/short_selling # 空売り比率
GET /markets/margin_interest # 信用取引残高
```

## 注意事項

- APIキーは`.env`ファイルで管理し、絶対にコミットしない
- API呼び出しはレート制限を考慮して適切に間隔を空ける
- データは可能な限りキャッシュして不要なAPI呼び出しを減らす
- エラー時は適切にリトライ処理を行う
- ログ出力を適切に行い、デバッグを容易にする
