# サラブレッドオークション データベース

楽天サラブレッドオークションからデータをスクレイピングし、分析用のデータベースを構築するシステムです。

## 重要なお知らせ

- **静的ファイルの使用**: 本システムはAPIを使用せず、静的JSONファイル（`horses_history.json`）からデータを読み込みます。
- **言語設定**: 本システムのドキュメントとチャットサポートは全て日本語で対応しています。

## 📚 ドキュメント

- **[プロジェクト仕様書](PROJECT_SPEC.md)** - 詳細な仕様・構成・運用方法
- **[AI用クイックリファレンス](AI_REFERENCE.md)** - AI支援開発用の簡易ガイド

## 🚀 クイックスタート

### 1. リポジトリのクローン

```bash
git clone https://github.com/furakutaru/SaraokuDB.git
cd SaraokuDB
```

### 2. バックエンドのセットアップ

```bash
# バックエンドディレクトリに移動
cd backend

# 仮想環境の作成と有効化（推奨）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# または
# .\venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements.txt
```

### 3. フロントエンドのセットアップ

```bash
# フロントエンドディレクトリに移動
cd ../frontend

# 依存関係のインストール
npm install
```

### 4. 環境変数の設定

```bash
# バックエンドディレクトリに移動
cd ../backend

# 環境変数ファイルの作成と編集
cp .env.example .env
# .envファイルを必要に応じて編集
```

### 5. データベースの初期化

```bash
# データベースの初期化
python -m database.init_db
```

### 6. アプリケーションの起動

#### バックエンドサーバーの起動

```bash
# バックエンドディレクトリで実行
python -m uvicorn main:app --reload
```

#### フロントエンド開発サーバーの起動（別ターミナル）

```bash
# フロントエンドディレクトリに移動
cd ../frontend

# 開発サーバーを起動
npm run dev
```

### 7. ブラウザで確認

- フロントエンド: http://localhost:3000
- バックエンドAPIドキュメント: http://localhost:8000/docs

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