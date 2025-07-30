# サラブレッドオークション データベース

楽天サラブレッドオークションからデータをスクレイピングし、分析用のデータベースを構築するシステムです。

## 📚 ドキュメント

- **[プロジェクト仕様書](PROJECT_SPEC.md)** - 詳細な仕様・構成・運用方法
- **[AI用クイックリファレンス](AI_REFERENCE.md)** - AI支援開発用の簡易ガイド

## 🚀 クイックスタート

### 1. 依存関係のインストール

```bash
# macOS/Linux
python3 setup.py

# Windows
python setup.py
```

### 2. 環境変数の設定

```bash
cp .env.example .env
# .envファイルを編集して必要な設定を行う
```

### 3. データベースの初期化

```bash
# macOS/Linux
python3 -m backend.database.init_db

# Windows
python -m backend.database.init_db
```

### 4. サーバーの起動

```bash
# バックエンド
# macOS/Linux
python3 -m uvicorn backend.main:app --reload

# Windows
python -m uvicorn backend.main:app --reload

# フロントエンド（別ターミナル）
cd static-frontend
npm install
npm run dev
```

## 📊 現在の機能

- **自動スクレイピング**: 木・日 23:59に楽天オークションからデータ取得
- **賞金更新**: 毎月1日にnetkeibaから最新賞金情報更新
- **統計分析**: 落札価格、成長率、ROI分析
- **馬詳細表示**: 血統、成績、疾病タグ、画像表示
- **検索・ソート**: 馬名、血統、価格での検索・ソート

## 🔄 自動化スケジュール

- **オークションスクレイピング**: 木曜・日曜 23:59
- **賞金情報更新**: 毎月1日 02:00
- **デプロイ**: GitHub Actions + Vercel自動化

## 📁 プロジェクト構造

```
SaraokuDB/
├── backend/                    # FastAPIバックエンド
│   ├── scrapers/               # スクレイピングモジュール
│   ├── services/               # ビジネスロジック
│   ├── scheduler/              # 自動実行スケジューラー
│   └── database/               # データベースモデル
├── static-frontend/            # Next.jsフロントエンド
│   ├── src/app/                # ページコンポーネント
│   ├── public/data/            # JSONデータファイル
│   └── components/             # UIコンポーネント
├── .github/workflows/          # GitHub Actions自動化
├── scripts/                    # スクレイピングスクリプト
└── data/                       # データベースファイル
```

## 🌐 アクセス

- **本番環境**: https://saraoku-db.vercel.app/
- **開発環境**: http://localhost:3000 (フロントエンド)
- **API**: http://localhost:8000/docs (バックエンド)

## 🔧 技術スタック

- **フロントエンド**: Next.js 15.3.5, TypeScript, Tailwind CSS
- **バックエンド**: FastAPI, Python 3.11, SQLite
- **デプロイ**: Vercel, GitHub Actions
- **スクレイピング**: BeautifulSoup, Selenium

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストやイシューの報告を歓迎します。

---

**注意**: このプロジェクトは教育・研究目的で作成されています。実際の運用時は、対象サイトの利用規約を確認してください。 