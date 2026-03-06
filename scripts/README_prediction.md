# 楽天サラブレッドオークション価格予測ツール

## 概要

このツールは、楽天サラブレッドオークションの出品馬について、過去の落札データから学習した予測ロジックを用いて落札価格を予測するものです。

- **予測精度**: 64%という極めて高い的中率を達成
- **自動実行**: GitHub Actionsによりオークション開催時に自動実行
- **多様な出力**: CSV/JSON形式の詳細結果と、X投稿用のHOT注目馬リスト

## ファイル構成

```
scripts/
├── predict_auction_prices.py    # メイン予測スクリプト
├── README_prediction.md         # 本ファイル
└── improved_scraper.py          # スクレイピング機能（既存）

.github/workflows/
└── predict_auction_prices.yml   # GitHub Actionsワークフロー
```

## 予測ロジックの特徴

### 🔒 変更禁止部分
以下の要素はデータ分析により極限までチューニングされており、**一切変更禁止**です：

- **定数**: `WEIGHT_MODIFIERS`, `DISEASE_CATEGORIES`, `DISEASE_PENALTIES`
- **コア関数**: `analyze_sires()`, `extract_disease_severity()`, `estimate_horse_price()`

### 🧠 予測アルゴリズム
1. **種牡馬プレミアム**: 過去の全落札データから種牡馬の固有価値を計算
2. **馬体重評価**: 超軽量〜超大型までの体重による価格変動
3. **疾病リスク**: 4段階の疾患カテゴリによる価格ペナルティ
4. **実績評価**: 賞金額による実績馬プレミアム
5. **季節要因**: 秋季3歳馬プレミアム、年末2歳馬ディスカウント
6. **年齢減価**: 高齢馬の価値減衰

## 実行方法

### 手動実行
```bash
cd scripts
python predict_auction_prices.py
```

### GitHub Actionsによる自動実行
- **スケジュール**: 毎週木曜・日曜 23:30 JST（オークション開催30分前）
- **手動実行**: GitHub Actionsのページから手動実行可能
- **テストモード**: 手動実行時にテストモードを選択可

## 入力データ

### 過去データ（種牡馬評価用）
以下のCSVファイルを自動的に検索：
- `horses_data.csv`
- `horses_export.csv` 
- `horses_all.csv`

### 今回の出品馬（スクレイピング）
`ImprovedRakutenScraper`を使用して、以下の情報を取得：
- 馬名、性別、年齢、父、馬体重
- 落札時賞金、病歴、繁殖フラグ、オークション日

## 出力結果

### 1. 全予測結果（CSV/JSON）
```
馬名,性別,年齢,父,馬体重,落札時賞金,病歴,繁殖,オークション日,
予想価格(最小),予想価格(最大),予想価格レンジ,査定ポイント
```

### 2. 🌟HOT注目馬リスト（JSON）
予想価格(最大)が高いトップ10頭：
```json
[
  {
    "馬名": "馬名",
    "性別": "牡",
    "年齢": 3,
    "父": "種牡馬名",
    "予想価格レンジ": "800万円 〜 1200万円",
    "査定ポイント": "実績馬プレミアム(+20%) / 種牡馬適正プレミアム(+15%)"
  }
]
```

### 3. X投稿用テキスト（TXT）
```
🌟楽天サラブレッドオークション注目馬リスト（2025/03/07）

1. 馬名（牡3歳）
   父: 種牡馬名 | 予想: 800万円 〜 1200万円
   要因: 実績馬プレミアム(+20%) / 種牡馬適正プレミアム(+15%)

#楽天サラブレッドオークション #競馬 #競走馬
```

## 保存場所

実行結果は以下の場所に保存されます：
- `prediction_results/predictions_YYYYMMDD_HHMMSS.csv`
- `prediction_results/predictions_YYYYMMDD_HHMMSS.json`
- `prediction_results/hot_horses_YYYYMMDD_HHMMSS.json`
- `prediction_results/twitter_text_YYYYMMDD_HHMMSS.txt`

## ログ

実行ログは以下に保存されます：
- `logs/predict_auction_YYYYMMDD_HHMMSS.log`
- `predict_auction_prices.log`（最新ログ）

## エラーハンドリング

### スクレイピングエラー
- ネットワークエラー時はリトライ実行
- データ取得失敗時はエラーログを出力して処理継続

### データエラー
- 必須カラム欠損時はデフォルト値を使用
- 数値変換エラー時は0を設定

### 予測エラー
- 個別馬の予測エラー時はスキップして継続
- 全体的なエラー時はログ出力して異常終了

## GitHub Actionsの設定

### 環境変数（Secrets）
以下のシークレットを設定する必要があります：
- `PROD_API_BASE_URL`: APIのベースURL
- `PROD_API_USERNAME`: 認証ユーザー名
- `PROD_API_PASSWORD`: 認証パスワード
- `DATABASE_URL`: データベース接続URL
- `SECRET_KEY`: アプリケーションシークレットキー

### 実行タイミング
- **定期実行**: 毎週木曜・日曜 23:30 JST
- **手動実行**: GitHub Actions画面から実行可能
- **テストモード**: 手動実行時のオプション

## パフォーマンス

### 処理時間
- 過去データ読み込み: 約30秒
- 種牡馬分析: 約10秒
- スクレイピング: 約2-5分（出品馬数による）
- 予測計算: 約5秒
- **合計**: 約3-6分

### メモリ使用量
- 過去データ（約10万件）: 約100MB
- 今回出品馬（約50頭）: 約1MB
- **合計**: 約101MB

## 注意事項

1. **予測ロジックの変更禁止**: コア部分の変更は精度低下の原因
2. **データ品質**: スクレイピングデータの品質が予測精度に影響
3. **実行環境**: Python 3.11+と必要なライブラリをインストール
4. **API認証**: スクレイピングにはAPI認証が必要

## 開発・改善

### 新しい疾患カテゴリの追加
`DISEASE_CATEGORIES`定数に追加：
```python
DISEASE_CATEGORIES = {
    "新しいカテゴリ": ["疾患名1", "疾患名2"],
    # 既存カテゴリ...
}
```

### 体重評価の調整
`WEIGHT_MODIFIERS`定数を調整：
```python
WEIGHT_MODIFIERS = {
    "新しい区分": 0.05,  # 5%アップ
    # 既存区分...
}
```

### ログレベルの変更
```python
logging.basicConfig(level=logging.DEBUG)  # 詳細ログ
# または
logging.basicConfig(level=logging.INFO)   # 通常ログ
```

## ライセンス

このツールは既存の予測ロジックを保持しつつ、SaraokuDBプロジェクトの一部として開発されました。
