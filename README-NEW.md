# サラブレッドオークションDB - 無料運用版

楽天サラブレッドオークションのデータをスクレイピングし、統計情報と馬の詳細情報を表示するWebアプリケーションです。

## 🎯 特徴

- **完全無料運用**: GitHub Actions + Vercelで無料で運用可能
- **自動スクレイピング**: 火・土曜日に自動でデータ更新
- **静的サイト**: Next.jsで高速な静的サイト
- **統計ダッシュボード**: 落札価格、成長率などの統計情報
- **馬詳細表示**: 血統、成績、画像などの詳細情報

## 📁 プロジェクト構成

```
/
├── .github/
│   └── workflows/
│       └── scrape.yml          # GitHub Actions自動スクレイピング
├── data/
│   └── horses.json             # スクレイピング結果データ
├── scripts/
│   └── scrape.py               # スクレイピング実行スクリプト
├── static-frontend/            # Next.js静的フロントエンド
│   ├── src/
│   │   ├── app/
│   │   │   └── page.tsx        # メインページ
│   │   └── components/
│   │       └── ui/             # UIコンポーネント
│   └── package.json
├── requirements-scrape.txt     # スクレイピング用依存関係
└── README-NEW.md
```

## 🚀 セットアップ手順

### 1. リポジトリのクローン

```bash
git clone <your-repo-url>
cd SaraokuDB
```

### 2. スクレイピングスクリプトの設定

```bash
# 依存関係のインストール
pip install -r requirements-scrape.txt

# スクレイピングテスト実行
python scripts/scrape.py
```

### 3. フロントエンドの設定

```bash
cd static-frontend
npm install
npm run dev
```

### 4. GitHub Actionsの設定

1. GitHubリポジトリにプッシュ
2. `.github/workflows/scrape.yml`が自動で設定される
3. 火・土曜日21:00（JST）に自動スクレイピング実行

### 5. Vercelでのデプロイ

1. [Vercel](https://vercel.com)にアカウント作成
2. GitHubリポジトリを接続
3. `static-frontend`ディレクトリを指定
4. 自動デプロイ開始

## 📊 データ構造

### horses.json

```json
{
  "metadata": {
    "last_updated": "2025-07-13T13:28:23.909241",
    "total_horses": 2,
    "average_price": 12590000,
    "average_growth_rate": 170.8,
    "horses_with_growth_data": 1,
    "next_auction_date": "2025-07-13"
  },
  "horses": [
    {
      "name": "タマモハヤブサ",
      "sex": "牡",
      "age": 3,
      "sold_price": 16680000,
      "seller": "飯島 利彦",
      "total_prize_start": 0.0,
      "total_prize_latest": 54966,
      "sire": "アニマルキングダム",
      "dam": "タマモクラリティー",
      "dam_sire": "ハーツクライ",
      "comment": "父のアニマルキングダムは...",
      "weight": 460,
      "race_record": "0-0-0-2",
      "primary_image": "https://...",
      "auction_date": "2025-07-13",
      "disease_tags": "なし",
      "netkeiba_url": "https://db.netkeiba.com/..."
    }
  ]
}
```

## 🔧 カスタマイズ

### スクレイピング対象の変更

`scripts/scrape.py`の`scrape_rakuten_auction`メソッドを編集：

```python
def scrape_rakuten_auction(self, auction_date: str = None) -> List[Dict]:
    # 実際のスクレイピング処理をここに実装
    # 現在はサンプルデータを使用
```

### スケジュールの変更

`.github/workflows/scrape.yml`のcron設定を編集：

```yaml
schedule:
  - cron: "0 12 * * 2,6"  # 火・土 21:00 JST
```

### フロントエンドのカスタマイズ

`static-frontend/src/app/page.tsx`を編集してデザインや機能を変更。

## 💰 運用コスト

- **GitHub Actions**: 月2,000分まで無料
- **Vercel**: 個人利用は完全無料
- **データ保存**: GitHubリポジトリ内のJSONファイル（無料）

## 🔄 自動化フロー

1. **火・土曜日21:00**: GitHub Actionsが自動実行
2. **スクレイピング**: 楽天オークションからデータ取得
3. **データ処理**: 統計情報計算、JSON形式で保存
4. **Gitコミット**: 変更を自動コミット・プッシュ
5. **Vercelデプロイ**: 静的サイトが自動更新

## 🛠️ トラブルシューティング

### スクレイピングが失敗する場合

1. ネットワーク接続を確認
2. 対象サイトの構造変更を確認
3. `scripts/scrape.py`のエラーハンドリングを確認

### フロントエンドが表示されない場合

1. `data/horses.json`が存在することを確認
2. Vercelのデプロイログを確認
3. 静的ファイルのパス設定を確認

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

---

**注意**: このプロジェクトは教育・研究目的で作成されています。実際の運用時は、対象サイトの利用規約を確認してください。 