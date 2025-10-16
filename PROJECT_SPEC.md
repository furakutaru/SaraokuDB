# サラオクDB プロジェクト仕様書

最終更新日: 2025-10-16

## 1. プロジェクト概要

サラオクDBは、楽天サラブレッドオークションのデータを収集・分析するためのシステムです。馬の血統情報、落札価格、賞金情報などを一元管理し、投資判断を支援します。

## 2. システムアーキテクチャ

### 2.1 全体構成

```
フロントエンド (Next.js 15)  ←→  バックエンド (FastAPI)  ←→  データソース (SQLite/JBIS/楽天オークション)
    │                                       │
    ▼                                       ▼
ブラウザ表示                    スクレイピング・データ処理・API提供
```

### 2.2 技術スタック

- **フロントエンド**
  - Next.js 15.3.5 (App Router)
  - TypeScript 5.0+
  - Tailwind CSS 3.4
  - shadcn/ui コンポーネント
  - React Query 5.0+

- **バックエンド**
  - Python 3.11+
  - FastAPI 0.110.0+
  - SQLAlchemy 2.0+
  - Alembic (データベースマイグレーション)
  - Pydantic 2.0+ (バリデーション)

- **データベース**
  - SQLite (開発環境)
  - 本番環境用のスケーラブルなデータベース対応可能

- **開発ツール**
  - Git 2.40+
  - pnpm 8.0+ / npm 9.0+
  - VSCode 推奨
  - Docker (オプション)

## 3. ディレクトリ構成

```
.
├── backend/                    # バックエンド関連
│   ├── app/                   # アプリケーションコード
│   │   ├── api/               # APIエンドポイント
│   │   │   └── v1/            # APIバージョン1
│   │   │       ├── horses.py  # 馬関連API
│   │   │       └── auctions.py # オークション関連API
│   │   ├── core/              # コア機能
│   │   │   ├── config.py      # 設定
│   │   │   └── security.py    # 認証・認可
│   │   ├── db/                # データベース関連
│   │   │   ├── models.py      # SQLAlchemyモデル
│   │   │   └── crud.py        # データベース操作
│   │   └── services/          # ビジネスロジック
│   │       ├── scraper.py     # スクレイピングサービス
│   │       └── analyzer.py    # 分析サービス
│   ├── tests/                 # テスト
│   │   ├── unit/              # ユニットテスト
│   │   └── integration/       # 統合テスト
│   ├── alembic/               # データベースマイグレーション
│   └── main.py                # アプリケーションエントリーポイント
│
├── frontend/                  # フロントエンドアプリケーション
│   ├── public/                # 静的ファイル
│   └── src/                   # ソースコード
│       ├── app/               # Next.js App Router
│       │   ├── (dashboard)    # ダッシュボード関連
│       │   ├── api/           # APIルート
│       │   ├── horses/        # 馬関連ページ
│       │   │   └── [id]/      # 馬詳細 (動的ルート)
│       ├── components/        # Reactコンポーネント
│       │   ├── ui/            # shadcn/ui コンポーネント
│       │   ├── horses/        # 馬関連コンポーネント
│       │   └── shared/        # 共通コンポーネント
│       └── lib/               # ユーティリティ関数
│           ├── api.ts         # APIクライアント
│           └── utils.ts       # ユーティリティ関数
│
├── scripts/                   # スクリプトとユーティリティ
│   ├── components/            # スクレイピングコンポーネント
│   │   ├── auction_info/      # オークション情報抽出
│   │   ├── comment/           # コメント抽出
│   │   └── extractors/        # データ抽出ユーティリティ
│   └── core/                  # コア機能
│       ├── cache/             # キャッシュ管理
│       ├── config/            # 設定
│       └── models/            # データモデル
│
├── data/                      # データファイル
│   └── horses.db             # SQLiteデータベース
│
└── docs/                      # ドキュメント
    └── SCRAPING_GUIDE.md     # スクレイピングガイド
```

## 4. 自動化スケジュール

### 4.1 定期的なスクレイピング

- **通常スクレイピング**
  - 毎週木・日曜日 23:59 JST に実行
  - 新規馬情報の取得と既存情報の更新

- **オークション開催日スクレイピング**
  - オークション開催日 20:00 JST に実行
  - 落札価格情報の取得

- **賞金情報更新**
  - 毎月1日 03:00 JST に実行
  - JBISからの賞金情報取得

### 4.2 メンテナンスタスク

- **日次バックアップ**
  - 毎日 04:00 JST に実行
  - データベースのバックアップをS3に保存
  - 過去30日分のバックアップを保持

- **週次メンテナンス**
  - 毎週月曜日 05:00 JST に実行
  - ログファイルのローテーション
  - 一時ファイルのクリーンアップ
  - データベースの最適化

## 5. データ構造

### 5.1 馬マスターテーブル (horses)

| カラム名 | 型 | 説明 | 必須 | 例 |
|---------|----|------|------|-----|
| id | UUID | 主キー | はい | 550e8400-e29b-41d4-a716-446655440000 |
| name | String | 馬名 | はい | キタサンブラック |
| sex | Enum('牡','牝','セ') | 性別 | はい | 牡 |
| age | Integer | 年齢 | はい | 5 |
| color | String | 毛色 | いいえ | 鹿毛 |
| sire | String | 父馬名 | はい | ブラックタイド |
| dam | String | 母馬名 | はい | シルクプライド |
| damsire | String | 母父名 | いいえ | サンデーサイレンス |
| breeder | String | 生産者 | いいえ | ノーザンファーム |
| owner | String | 馬主 | いいえ | サンデーレーシング |
| trainer | String | 調教師 | いいえ | 池江泰寿 |
| total_prize_start | Float | オークション時点の総賞金(万円) | はい | 1500.5 |
| total_prize_latest | Float | 最新の総賞金(万円) | はい | 2500.5 |
| image_url | String | 画像URL | いいえ | https://example.com/image.jpg |
| jbis_url | String | JBIS URL | いいえ | https://www.jbis.or.jp/horse/... |
| auction_url | String | オークションURL | いいえ | https://www.rakuten-keiba.co.jp/... |
| created_at | DateTime | 作成日時 | はい | 2023-01-01 12:00:00 |
| updated_at | DateTime | 更新日時 | はい | 2023-01-01 12:00:00 |

### 5.2 オークション履歴テーブル (auction_history)

| カラム名 | 型 | 説明 | 必須 | 例 |
|---------|----|------|------|-----|
| id | UUID | 主キー | はい | 660e8400-e29b-41d4-a716-446655440001 |
| horse_id | UUID | 馬ID (外部キー) | はい | 550e8400-e29b-41d4-a716-446655440000 |
| auction_date | Date | オークション日 | はい | 2023-01-15 |
| sold_price | Integer | 落札価格(円) | いいえ | 10000000 |
| total_prize_start | Float | オークション時点の総賞金(万円) | はい | 0.0 |
| total_prize_latest | Float | 最新の総賞金(万円) | はい | 1500.5 |
| weight | Float | 馬体重(kg) | いいえ | 480.5 |
| seller | String | 売り主 | いいえ | ノーザンファーム |
| is_unsold | Boolean | 未落札フラグ | はい | false |
| comment | Text | コメント | いいえ | 体高16.1 |
| created_at | DateTime | 作成日時 | はい | 2023-01-15 12:00:00 |
| updated_at | DateTime | 更新日時 | はい | 2023-01-15 12:00:00 |

## 6. API仕様

### 6.1 エンドポイント一覧

#### 馬関連

- `GET /api/v1/horses` - 馬の一覧を取得
- `GET /api/v1/horses/{horse_id}` - 馬の詳細を取得
- `GET /api/v1/horses/search` - 馬を検索
- `GET /api/v1/horses/{horse_id}/history` - 馬のオークション履歴を取得

#### オークション関連

- `GET /api/v1/auctions` - オークション一覧を取得
- `GET /api/v1/auctions/{auction_id}` - オークションの詳細を取得
- `GET /api/v1/auctions/upcoming` - 今後のオークションを取得

### 6.2 認証

- APIキー認証を使用
- ヘッダーに `X-API-Key` を設定

## 7. フロントエンド仕様

### 7.1 画面構成

1. **トップページ**
   - お知らせ
   - 直近のオークション情報
   - 注目の馬

2. **馬一覧ページ**
   - 検索・フィルタリング
   - ソート機能
   - ページネーション

3. **馬詳細ページ**
   - 基本情報
   - 血統情報
   - オークション履歴
   - 賞金推移
   - RIO分析

4. **分析ページ**
   - 血統別分析
   - 価格帯別分析
   - 年次比較

### 7.2 主な機能

- **RIO（Return on Investment）計算**
  - 計算式: `RIO = (落札後に稼いだ賞金総額) ÷ 落札価格`
  - 落札後に稼いだ賞金総額 = `現在の総賞金 - オークション時の総賞金`
  - 表示: パーセンテージ（例: 15.0%）

- **検索・フィルタリング**
  - 馬名検索
  - 血統検索
  - 価格帯フィルタ
  - 賞金額フィルタ
  - 性別フィルタ
  - 年齢フィルタ

- **ソート機能**
  - 落札価格（昇順/降順）
  - 賞金（昇順/降順）
  - RIO（昇順/降順）
  - オークション日（昇順/降順）

## 8. 開発環境構築

### 8.1 バックエンド開発環境

```bash
# リポジトリをクローン
git clone https://github.com/furakutaru/SaraokuDB.git
cd SaraokuDB/backend

# 仮想環境の作成と有効化
python -m venv venv
source venv/bin/activate  # Linux/macOS
# .\venv\Scripts\activate  # Windows

# 依存関係のインストール
pip install -r requirements-dev.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集

# データベースの初期化
alembic upgrade head

# テストの実行
pytest

# 開発サーバーの起動
uvicorn app.main:app --reload
```

### 8.2 フロントエンド開発環境

```bash
# フロントエンドディレクトリに移動
cd ../frontend

# 依存関係のインストール
pnpm install  # または npm install

# 開発サーバーの起動
pnpm dev  # または npm run dev
```

## 9. デプロイ

### 9.1 本番環境

- **フロントエンド**: Vercel
- **バックエンド**: 未定（現在はVercel Serverless Functionsを検討中）
- **データベース**: SQLite（S3でバックアップ）

### 9.2 CI/CD

GitHub Actionsを使用して以下のワークフローを実行:

1. **テスト** (プルリクエスト時)
   - バックエンドのテスト
   - フロントエンドのテスト
   - コードカバレッジの計測

2. **デプロイ** (mainブランチにマージ時)
   - フロントエンドのビルドとデプロイ
   - バックエンドのデプロイ
   - データベースのマイグレーション

## 10. 今後の開発予定

### 10.1 予定されている機能

- [ ] ユーザー認証機能
- [ ] お気に入り機能
- [ ] メール通知機能
- [ ] より詳細な分析機能
- [ ] モバイルアプリの開発

### 10.2 技術的負債

- [ ] テストカバレッジの向上
- [ ] エラーハンドリングの改善
- [ ] パフォーマンス最適化
- [ ] セキュリティ対策の強化

## 11. ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) で公開されています。

## 12. 連絡先

プロジェクトに関するお問い合わせは、GitHubのIssueまたはプルリクエストでお願いします。
