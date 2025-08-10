# サラオクDB

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-13.4.12-000000?logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000?logo=vercel)](https://vercel.com/)

楽天サラブレッドオークションからデータをスクレイピングし、馬の血統・落札価格・賞金情報などを分析するためのデータベースシステムです。

## ✨ 主な機能

- **自動スクレイピング**: 楽天オークションから馬情報を自動収集
- **賞金追跡**: オークション時点と最新の賞金を比較
- **RIO分析**: 投資収益率（Return on Investment）を自動計算
- **検索・フィルタリング**: 条件に応じた馬の検索・ソート機能
- **レスポンシブデザイン**: PC・タブレット・スマートフォン対応

## 🚨 重要なお知らせ

- **静的ファイルの使用**: 本システムはAPIを使用せず、静的JSONファイル（`horses_history.json`）からデータを読み込みます。
- **言語設定**: 本システムのドキュメントとチャットサポートは全て日本語で対応しています。
- **データ更新**: オークション開催日に自動でデータが更新されます（木・日 23:59）
- **テスト環境**: テストモードでの実行方法は[AI_REFERENCE.md](AI_REFERENCE.md)を参照してください。

## 📚 ドキュメント

| ドキュメント | 説明 |
|------------|------|
| [プロジェクト仕様書](PROJECT_SPEC.md) | プロジェクトの詳細な仕様・構成・運用方法 |
| [AI用クイックリファレンス](AI_REFERENCE.md) | AI支援開発用の簡易ガイド |
| [スクレイピングガイド](docs/SCRAPING_GUIDE.md) | スクレイピングの運用・保守手順 |

## 🎯 主な特徴

- **最新技術スタック**: Next.js 15 + FastAPI + SQLite
- **完全自動化**: GitHub ActionsによるCI/CDパイプライン
- **無料運用**: Vercelの無料枠で完全運用可能
- **データ可視化**: 直感的なUIでデータを可視化

## 🚀 クイックスタート

### 前提条件

- Node.js 18+
- Python 3.11+
- Git
- pnpm (推奨) または npm

### 1. リポジトリのクローン

```bash
git clone https://github.com/furakutaru/SaraokuDB.git
cd SaraokuDB
```

### 2. 依存関係のインストール

```bash
# フロントエンド
cd static-frontend
pnpm install  # または npm install

# バックエンド
cd ../backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
# Windows: .\venv\Scripts\activate
pip install -r requirements.txt
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

## 🛠 主な機能

### データ収集
- **自動スクレイピング**: 木・日 23:59に楽天オークションからデータ取得
- **賞金更新**: 定期的にJBISから最新賞金情報を更新
- **画像取得**: 馬の画像を自動収集

### 分析機能
- **RIO分析**: 投資収益率を自動計算
- **成長率追跡**: 賞金の伸び率を可視化
- **統計情報**: 平均落札価格、最高落札価格などの統計

### 検索・フィルタリング
- **詳細検索**: 馬名、血統、価格帯などでの検索
- **ソート機能**: 落札価格、賞金、成長率などでソート
- **フィルタリング**: 性別、年齢、疾病タグなどでフィルタリング

### その他
- **レスポンシブデザイン**: あらゆるデバイスで最適な表示
- **ダークモード対応**: 目に優しい表示モード
- **オフライン対応**: 一度アクセスしたデータはオフラインでも閲覧可能

## ⏰ 自動化スケジュール

### 定期的なタスク
| タスク | スケジュール | 説明 |
|-------|------------|------|
| オークションスクレイピング | 木・日 23:59 (JST) | 楽天オークションから最新情報を取得 |
| 賞金情報更新 | 毎月1日 02:00 (JST) | JBISから最新の賞金情報を取得 |
| データバックアップ | 毎日 03:00 (JST) | データベースのバックアップを取得 |

### デプロイフロー
1. GitHubにプッシュ
2. GitHub Actionsが自動でテストを実行
3. テスト成功時にVercelに自動デプロイ
4. 本番環境に反映

## 📁 プロジェクト構造

```
SaraokuDB/
├── backend/                    # FastAPIバックエンド
│   ├── scrapers/               # スクレイピングモジュール
│   │   ├── rakuten_scraper.py  # 楽天オークションスクレイパー
│   │   └── jbis_scraper.py     # JBISスクレイパー
│   ├── services/               # ビジネスロジック
│   ├── scheduler/              # 自動実行スケジューラー
│   └── database/               # データベースモデル
│       ├── models.py           # SQLAlchemyモデル
│       └── crud.py             # データベース操作ユーティリティ
├── static-frontend/            # Next.jsフロントエンド
│   ├── src/app/                # ページコンポーネント (App Router)
│   │   ├── horses/             # 馬関連ページ
│   │   ├── dashboard/          # ダッシュボードページ
│   │   └── api/                # APIルート
│   ├── public/data/            # 静的JSONデータ
│   └── components/             # 共通UIコンポーネント
│       ├── ui/                 # 基本UIコンポーネント
│       └── horses/             # 馬関連コンポーネント
├── .github/workflows/          # GitHub Actionsワークフロー
│   ├── scrape.yml              # スクレイピング自動化
│   ├── deploy.yml              # デプロイ自動化
│   └── test.yml                # テスト自動化
├── scripts/                    # スクレイピングスクリプト
├── docs/                       # ドキュメント
│   ├── API.md                  # API仕様書
│   └── CONTRIBUTING.md         # コントリビューションガイド
├── tests/                      # テストコード
│   ├── unit/                   # ユニットテスト
│   └── e2e/                    # E2Eテスト
└── data/                       # データベースファイル
    ├── horses.db               # SQLiteデータベース
    └── migrations/             # データベースマイグレーション
```

## 🌐 アクセス

### 本番環境
- **URL**: [https://saraoku-db.vercel.app/](https://saraoku-db.vercel.app/)
- **ステータス**: [![Vercel](https://img.shields.io/github/deployments/furakutaru/SaraokuDB/production?label=Vercel&logo=vercel)](https://vercel.com/furakutaru/SaraokuDB)

### 開発環境
- **フロントエンド**: http://localhost:3000
- **バックエンドAPI**: http://localhost:8000
- **APIドキュメント**: http://localhost:8000/docs
- **Swagger UI**: http://localhost:8000/redoc

### モニタリング
- **Vercel Analytics**: パフォーマンス監視
- **GitHub Actions**: CI/CDパイプライン
- **Sentry**: エラートラッキング

## 🛠 技術スタック

### フロントエンド
- **フレームワーク**: [Next.js 15.3.5](https://nextjs.org/) (App Router)
- **言語**: [TypeScript 5.2](https://www.typescriptlang.org/)
- **スタイリング**: [Tailwind CSS](https://tailwindcss.com/) + [shadcn/ui](https://ui.shadcn.com/)
- **状態管理**: [Zustand](https://github.com/pmndrs/zustand)
- **データフェッチ**: [TanStack Query](https://tanstack.com/query/latest)
- **フォーム**: [React Hook Form](https://react-hook-form.com/)
- **バリデーション**: [Zod](https://zod.dev/)

### バックエンド
- **フレームワーク**: [FastAPI](https://fastapi.tiangolo.com/)
- **言語**: [Python 3.11](https://www.python.org/)
- **データベース**: [SQLite](https://www.sqlite.org/index.html)
- **ORM**: [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/)
- **非同期処理**: [asyncio](https://docs.python.org/3/library/asyncio.html)
- **テスト**: [pytest](https://docs.pytest.org/)

### スクレイピング
- **HTMLパース**: [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- **ブラウザ自動化**: [Selenium](https://www.selenium.dev/)
- **HTTPクライアント**: [httpx](https://www.python-httpx.org/)
- **HTMLキャッシュ**: ディスクベースキャッシュ

### インフラ
- **ホスティング**: [Vercel](https://vercel.com/)
- **CI/CD**: [GitHub Actions](https://github.com/features/actions)
- **パッケージマネージャー**: [pnpm](https://pnpm.io/) / [pip](https://pypi.org/project/pip/)
- **コンテナ**: [Docker](https://www.docker.com/) (開発用)

### 開発ツール
- **エディタ**: [VS Code](https://code.visualstudio.com/)
- **リンター**: [ESLint](https://eslint.org/), [Prettier](https://prettier.io/)
- **型チェック**: [TypeScript](https://www.typescriptlang.org/), [mypy](http://mypy-lang.org/)
- **テストランナー**: [Jest](https://jestjs.io/), [Testing Library](https://testing-library.com/)

## 📄 ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) の下で公開されています。

```
MIT License

Copyright (c) 2025 サラオクDB開発チーム

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 👥 貢献

バグ報告や機能要望、プルリクエストは大歓迎です！

### 貢献の手順

1. イシューを作成して、作業内容を報告
2. リポジトリをフォークして、新しいブランチを作成
3. 変更をコミットしてプッシュ
4. プルリクエストを作成

### 行動規範

このプロジェクトは [Contributor Covenant](https://www.contributor-covenant.org/) 行動規範に従います。

## 🙏 謝辞

- データ提供: 楽天オークション、JBISサーチ
- アイコン: [Lucide Icons](https://lucide.dev/)
- 開発環境: [GitHub Codespaces](https://github.com/features/codespaces)

---

## ⚠️ 免責事項

このプロジェクトは教育・研究目的で作成されています。

- 実際の運用時は、対象サイトの利用規約を必ず確認してください。
- 本ソフトウェアの使用によって生じたいかなる損害についても、開発者は責任を負いません。
- スクレイピングは対象サイトのサーバーに負荷をかけないよう、適切な間隔を空けて実行してください。
- 本プロジェクトで収集したデータは、著作権法や個人情報保護法に従って適切に取り扱ってください。

## 📬 連絡先

質問やご意見がある場合は、[GitHub Issues](https://github.com/furakutaru/SaraokuDB/issues) までお気軽にどうぞ。

---

**最終更新日**: 2025年8月11日