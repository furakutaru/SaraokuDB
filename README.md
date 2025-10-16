# サラオクDB

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-15.3.5-000000?logo=next.js)](https://nextjs.org/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-000000?logo=vercel)](https://vercel.com/)

楽天サラブレッドオークションのデータを収集・分析するためのデータベースシステムです。馬の血統情報、落札価格、賞金情報などを一元管理し、投資判断を支援します。

## ✨ 主な機能

- **自動データ収集**
  - 楽天サラブレッドオークションからの馬情報スクレイピング
  - JBISからの賞金情報自動取得
  - 定期的なデータ更新（週2回）

- **データ分析**
  - 落札価格と賞金情報の分析
  - RIO（Return on Investment）計算
  - 血統別パフォーマンス分析

- **直感的なWebインターフェース**
  - レスポンシブデザイン（PC/タブレット/スマートフォン対応）
  - 高度な検索・フィルタリング機能
  - データの可視化

## 🚀 セットアップ

### 前提条件

- Node.js 18 以上
- Python 3.11 以上
- pnpm または npm
- Git

### インストール手順

1. リポジトリをクローン:
   ```bash
   git clone https://github.com/furakutaru/SaraokuDB.git
   cd SaraokuDB
   ```

2. バックエンドのセットアップ:
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
   
   # 環境変数の設定
   cp .env.example .env
   # .envファイルを必要に応じて編集
   
   # データベースの初期化
   python -m database.init_db
   ```

3. フロントエンドのセットアップ:
   ```bash
   # フロントエンドディレクトリに移動
   cd ../frontend
   
   # 依存関係のインストール
   pnpm install  # または npm install
   ```

## 🚀 開発サーバーの起動

### バックエンドサーバーの起動

```bash
# バックエンドディレクトリで実行
cd backend
python -m uvicorn main:app --reload
```

### フロントエンド開発サーバーの起動（別ターミナル）

```bash
# フロントエンドディレクトリで実行
cd frontend
pnpm dev  # または npm run dev
```

アプリケーションは以下のURLでアクセス可能です：
- フロントエンド: http://localhost:3000
- バックエンドAPI: http://localhost:8000
- APIドキュメント: http://localhost:8000/docs

## 🛠 開発

### テストの実行

```bash
# バックエンドテスト
cd backend
pytest

# フロントエンドテスト
cd ../frontend
pnpm test  # または npm test
```

### コードフォーマット

```bash
# バックエンド
cd backend
black .
isort .

# フロントエンド
cd ../frontend
pnpm format  # または npm run format
```

## 📁 プロジェクト構成

```
.
├── backend/                    # バックエンド関連
│   ├── app/                   # アプリケーションコード
│   │   ├── api/               # APIエンドポイント
│   │   ├── core/              # コア機能
│   │   ├── db/                # データベース関連
│   │   └── services/          # ビジネスロジック
│   ├── tests/                 # テスト
│   ├── alembic/               # データベースマイグレーション
│   └── main.py                # アプリケーションエントリーポイント
│
├── frontend/                  # フロントエンドアプリケーション
│   ├── public/                # 静的ファイル
│   └── src/                   # ソースコード
│       ├── app/               # Next.js App Router
│       ├── components/        # Reactコンポーネント
│       └── lib/               # ユーティリティ関数
│
├── scripts/                   # スクリプトとユーティリティ
│   ├── components/            # スクレイピングコンポーネント
│   └── core/                  # コア機能
│
├── data/                      # データファイル
│   └── horses.db             # SQLiteデータベース
│
└── docs/                      # ドキュメント
    └── SCRAPING_GUIDE.md     # スクレイピングガイド
```

## 🤝 貢献

1. リポジトリをフォークする
2. フィーチャーブランチを作成する (`git checkout -b feature/AmazingFeature`)
3. 変更をコミットする (`git commit -m 'Add some AmazingFeature'`)
4. ブランチにプッシュする (`git push origin feature/AmazingFeature`)
5. プルリクエストを開く

## 📄 ライセンス

このプロジェクトはMITライセンスの下でライセンスされています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## ✉️ 連絡先

プロジェクトに関するご質問やご意見がございましたら、以下のいずれかまでお気軽にご連絡ください：

- GitHub Issues: [Issues](https://github.com/furakutaru/SaraokuDB/issues)

---

<div align="center">
  <sub>Built with ❤︎ by <a href="https://github.com/furakutaru">furakutaru</a></sub>
</div>
