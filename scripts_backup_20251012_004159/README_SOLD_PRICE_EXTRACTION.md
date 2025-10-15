# 落札価格抽出機能のドキュメント

このドキュメントでは、楽天競馬オークションのHTMLから落札価格を抽出する機能について説明します。

## 機能概要

- `extract_sold_price.py`: 楽天競馬オークションのHTMLから落札価格を抽出するモジュール
- `test_sold_price_extraction.py`: 落札価格抽出機能をテストするためのスクリプト
- `process_horse_details.py`: 馬の詳細情報を処理するスクリプト（落札価格抽出機能を統合済み）

## 落札価格抽出のロジック

落札価格は以下の優先順位で抽出を試みます：

1. **itemprop="price" 属性**を持つ要素を検索（最も確実な方法）
2. 「現在価格」というテキストを含む要素を検索
3. 価格ボックス（`priceBox`、`price-box`、`price_box`クラス）を検索
4. 正規表現を使用してテキスト全体から価格を検索
   - 「落札価格」の後に続く数値
   - 「123,456円」形式の数値
   - 「123,456万円」形式の数値

## 使用方法

### 落札価格抽出モジュールの使用例

```python
from extract_sold_price import extract_sold_price

# HTMLファイルを読み込む
with open('horse_detail.html', 'r', encoding='utf-8') as f:
    html_content = f.read()

# 落札価格を抽出
price = extract_sold_price(html_content)
if price is not None:
    print(f"落札価格: ¥{price:,}")
else:
    print("落札価格を見つけることができませんでした")
```

### テストスクリプトの使用例

単一のHTMLファイルをテストする場合:
```bash
python test_sold_price_extraction.py path/to/horse_detail.html
```

ディレクトリ内の全HTMLファイルをテストする場合:
```bash
python test_sold_price_extraction.py path/to/html/directory/
```

### process_horse_details.py での使用

`process_horse_details.py` には既に落札価格抽出機能が統合されています。
馬の詳細情報を処理する際に、自動的に落札価格も抽出され、結果のJSONに `sold_price` フィールドとして追加されます。

## エラーハンドリング

- 落札価格が見つからない場合は `None` を返します
- エラーが発生した場合はログに記録され、`None` を返します

## ログ

- ログは `process_horse_details.log` に出力されます
- ログレベルは `DEBUG` に設定されているため、詳細なデバッグ情報が記録されます

## 注意事項

- 落札価格の表示形式が変更された場合、正しく抽出できない可能性があります
- テストモードでは、キャッシュされたHTMLを使用してテストできます
