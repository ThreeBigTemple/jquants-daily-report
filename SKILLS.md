# Skills - J-Quants Daily Report

## 必要なスキル・知識

### 1. J-Quants API
- **認証フロー**: リフレッシュトークン → IDトークン
- **Standardプラン制限**: 利用可能エンドポイントとデータ範囲
- **レート制限**: 適切な呼び出し間隔
- **参考**: https://jpx.gitbook.io/j-quants-ja

### 2. Python開発
- **uv**: パッケージ管理・仮想環境（pipは使用禁止）
- **pandas**: データフレーム操作、時系列処理
- **型ヒント**: 全関数に型アノテーション必須
- **テスト**: pytest、モック活用

### 3. 株式市場知識
- **指数**: 日経225、TOPIX、グロース市場250
- **業種分類**: 東証33業種
- **テクニカル指標**: 騰落レシオ、移動平均乖離率
- **需給指標**: 投資部門別売買、信用残

### 4. Markdown
- **テーブル記法**: パイプ区切り
- **見出し構造**: 適切な階層
- **可読性**: 数値フォーマット

---

## スキル適用ルール

### コード生成時
```python
# 型ヒント必須
def calculate_return(price: float, prev_price: float) -> float:
    """騰落率を計算する。
    
    Args:
        price: 当日終値
        prev_price: 前日終値
        
    Returns:
        騰落率（%表示）
    """
    return (price - prev_price) / prev_price * 100
```

### API呼び出し時
```python
# レート制限対応
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def fetch_data(endpoint: str) -> dict:
    time.sleep(1)  # レート制限
    response = requests.get(endpoint, headers=headers)
    response.raise_for_status()
    return response.json()
```

### レポート生成時
```markdown
## 市場概況

| 指数 | 終値 | 前日比 | 騰落率 |
|------|-----:|-------:|-------:|
| 日経225 | 38,500.00 | +250.00 | +0.65% |
```

---

## エラー対処パターン

### API認証エラー
1. リフレッシュトークンの有効期限確認（1週間）
2. IDトークンの再取得
3. 環境変数の確認

### データ取得エラー
1. キャッシュからの読み込みを試行
2. 日付範囲の確認（営業日のみ）
3. エンドポイントの利用可能性確認

### レポート生成エラー
1. 必須データの存在確認
2. 数値フォーマットのNaN対応
3. 出力ディレクトリの存在確認
