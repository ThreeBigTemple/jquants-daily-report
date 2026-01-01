# CLAUDE.md - J-Quants Daily Report System

## プロジェクト概要

J-Quants API（Standardプラン）を利用した日次株式市場レポート自動生成システム。
毎日の市場クローズ後に実行し、Markdown形式のレポートを出力する。

## 技術スタック

- **Python**: 3.11+
- **パッケージ管理**: uv（pipは使用禁止）
- **主要ライブラリ**: pandas, requests, python-dotenv, numpy
- **出力形式**: Markdown

## コマンドリファレンス

```bash
# 仮想環境のセットアップ
uv venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 依存関係のインストール
uv sync

# パッケージの追加
uv add <package-name>

# 開発用パッケージの追加
uv add --dev <package-name>

# アプリケーション実行
uv run python -m jquants_report

# テスト実行
uv run pytest

# 型チェック
uv run mypy src/

# リント
uv run ruff check src/
uv run ruff format src/
```

## ディレクトリ構造

```
src/jquants_report/
├── main.py          # CLI エントリーポイント
├── config.py        # 設定・環境変数管理
├── api/             # J-Quants API クライアント
├── data/            # データ取得・キャッシュ
├── analysis/        # 分析ロジック
└── report/          # レポート生成
```

## コーディング規約

### 全般
- 型ヒントを必ず使用する
- docstringはGoogle形式で記述
- 関数は単一責任の原則に従う
- マジックナンバーは定数として定義

### 命名規則
- クラス: PascalCase
- 関数・変数: snake_case
- 定数: UPPER_SNAKE_CASE
- プライベート: _prefix

### エラーハンドリング
- カスタム例外クラスを定義して使用
- API呼び出しは必ずtry-exceptで囲む
- エラーログは適切なレベルで出力

### API呼び出し
- レート制限を考慮（1秒間隔を推奨）
- リトライロジックを実装（exponential backoff）
- トークンの自動更新を実装

## 環境変数

```
JQUANTS_EMAIL=your-email@example.com
JQUANTS_PASSWORD=your-password
JQUANTS_REFRESH_TOKEN=xxx  # 取得後に設定
REPORT_OUTPUT_DIR=./reports
CACHE_DIR=./data
LOG_LEVEL=INFO
```

## J-Quants API 認証フロー

1. メールアドレス/パスワードでリフレッシュトークン取得
2. リフレッシュトークンでIDトークン取得（有効期限24時間）
3. IDトークンをAuthorizationヘッダーに設定してAPI呼び出し

## レポート出力

- ファイル名: `market_report_YYYYMMDD.md`
- 出力先: `./reports/`
- 過去レポートは日付別に保持

## テスト

- ユニットテストは `tests/` 配下に配置
- モックを使用してAPI呼び出しをテスト
- カバレッジ80%以上を目標

## デバッグ

```bash
# 詳細ログを出力
LOG_LEVEL=DEBUG uv run python -m jquants_report

# 特定の日付でレポート生成
uv run python -m jquants_report --date 2024-01-15

# ドライラン（API呼び出しなし、キャッシュのみ使用）
uv run python -m jquants_report --dry-run
```

## 既知の制約

- Standardプランでは一部データに遅延あり
- 日次データは市場クローズ後に更新される
- API呼び出し回数に制限あり

## 参考リンク

- [J-Quants API ドキュメント](https://jpx.gitbook.io/j-quants-ja)
- [J-Quants API リファレンス](https://jpx.gitbook.io/j-quants-ja/api-reference)
