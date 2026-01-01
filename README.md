# jquants-daily-report

## Overview
本プロジェクトは、日本株市場データ（J-Quants API）を用いて  
**市場全体・セクター・個別指標を自動分析し、日次レポートとして出力するシステム**です。

データ取得から分析、レポート生成までを Python で一貫して設計・実装しており、  
**実務での市場分析・定例レポート自動化を想定した構成**になっています。

---

## 🔍 What This Project Solves
- 毎日の市場データ収集・分析を手作業で行う負担
- 市場全体を俯瞰する定型レポート作成の自動化
- API 制限を考慮した効率的なデータ取得・キャッシュ

---

## 🏗️ System Architecture

```text
J-Quants API
    ↓
Data Fetcher
    ↓
SQLite Cache
    ↓
Analysis Engine
    ↓
Markdown Report
```

---

## ⚙️ Key Features
- J-Quants API を利用した株価・市場データ取得
- SQLite を用いたローカルキャッシュ設計
- 市場・セクター単位の分析ロジック
- 日次レポートの Markdown 自動生成
- CLI ベースでの実行
- テスト・型チェックによる品質担保

---

## 🧠 My Contribution
本プロジェクトは **個人開発** で、以下をすべて担当しています。

- API クライアント設計・実装
- データ取得・キャッシュ戦略設計
- 分析ロジック設計（市場指標・集計）
- SQLite スキーマ設計
- レポート生成ロジック
- CLI インターフェース設計
- pytest によるテスト実装
- 型ヒントによる可読性・保守性向上

---

## 📊 Sample Output

```markdown
# Daily Market Report

## Market Overview
- Nikkei Average: +1.2%
- TOPIX: +0.9%

## Sector Performance
- Semiconductor: +2.3%
- Banking: -0.4%
```
（※ 実際の出力例は `docs/sample_report.md` を参照）

---

## 🛠️ Tech Stack
- Python
- Pandas / NumPy
- SQLite
- J-Quants API
- pytest
- mypy
- Markdown

---

## 🚀 How to Run

```bash
git clone https://github.com/ThreeBigTemple/jquants-daily-report
cd jquants-daily-report

pip install -r requirements.txt
python main.py
```

※ API Key は `.env` に設定してください（`.env.example` 参照）

---

## 🎯 Intended Use Case
- 金融市場の定期分析・社内レポート自動化
- データ分析パイプラインのサンプル実装
- API × Python × SQLite の設計例

---

## 📌 For Recruiters
このリポジトリは **ポートフォリオ用途** として整備しています。

特に以下の点をご覧ください：
- データ取得〜分析〜出力までの一貫設計
- キャッシュ設計と API 利用効率
- 分析ロジックの構成
