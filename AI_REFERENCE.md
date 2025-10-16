# サラオクDB AI用クイックリファレンス

最終更新日: 2025-10-16

## 🚀 プロジェクト概要

### 基本情報
- **プロジェクト名**: サラオクDB
- **目的**: 楽天サラブレッドオークションのデータを収集・分析するツール
- **本番URL**: [https://saraoku-db.vercel.app/](https://saraoku-db.vercel.app/)
- **開発URL**: http://localhost:3000
- **最終更新**: 2025年10月16日

### 技術スタック
- **フロントエンド**: Next.js 15.3.5 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **バックエンド**: FastAPI, Python 3.11, SQLAlchemy 2.0, Alembic
- **データベース**: SQLite (開発), 本番環境はスケーラブルなデータベース対応
- **デプロイ**: Vercel (フロントエンド), GitHub Actions (CI/CD)
- **スクレイピング**: BeautifulSoup, Selenium, httpx

### 主な機能
- 楽天オークションからの馬データ自動収集
- JBISからの賞金情報取得
- RIO (Return on Investment) 分析
- 詳細な検索・フィルタリング機能
- レスポンシブデザイン

## 📁 プロジェクト構成

### フロントエンド (Next.js 15.3.5)
```
frontend/
├── public/                    # 静的ファイル
│   └── data/                  # 静的データファイル
└── src/
    ├── app/                   # App Router ベースのページ
    │   ├── (dashboard)        # ダッシュボード関連
    │   ├── api/               # APIルート
    │   ├── horses/            # 馬関連ページ
    │   │   ├── [id]/          # 馬詳細 (動的ルート)
    │   │   │   └── page.tsx   # 馬詳細ページ
    │   │   └── page.tsx       # 馬一覧ページ
    │   └── page.tsx           # ホームページ
    ├── components/            # 再利用可能なコンポーネント
    │   ├── ui/                # shadcn/ui コンポーネント
    │   ├── horses/            # 馬関連コンポーネント
    │   │   ├── HorseCard.tsx  # 馬カード
    │   │   ├── HorseFilters.tsx # フィルターコンポーネント
    │   │   └── HorseStats.tsx # 統計情報
    │   └── shared/            # 共通コンポーネント
    └── lib/                   # ユーティリティ関数
        ├── api.ts             # APIクライアント
        └── utils.ts           # ユーティリティ関数
```

### バックエンド (FastAPI)
```
backend/
├── app/
│   ├── api/                   # APIエンドポイント
│   │   └── v1/                # APIバージョン1
│   │       ├── horses.py      # 馬関連API
│   │       └── auctions.py    # オークション関連API
│   ├── core/                  # コア機能
│   │   ├── config.py          # 設定
│   │   └── security.py        # 認証・認可
│   ├── db/                    # データベース関連
│   │   ├── models.py          # SQLAlchemyモデル
│   │   └── crud.py            # データベース操作
│   └── services/              # ビジネスロジック
│       ├── scraper.py         # スクレイピングサービス
│       └── analyzer.py        # 分析サービス
├── tests/                     # テスト
│   ├── unit/                  # ユニットテスト
│   └── integration/           # 統合テスト
├── alembic/                   # データベースマイグレーション
└── main.py                    # アプリケーションエントリーポイント
```

### スクリプト
```
scripts/
├── components/                # スクレイピングコンポーネント
│   ├── auction_info/          # オークション情報抽出
│   ├── comment/               # コメント抽出
│   └── extractors/            # データ抽出ユーティリティ
└── core/                      # コア機能
    ├── cache/                 # キャッシュ管理
    ├── config/                # 設定
    └── models/                # データモデル
```

## 📊 データ仕様

### データ型と形式

#### 1. 価格（落札価格など）
- **保存形式**: 円単位の整数（例: `10000000`）
- **表示形式**: カンマ区切り + 円（例: `10,000,000円`）
- **TypeScript型**: `number | null`
- **フォーマット例**:
  ```typescript
  const formatPrice = (price: number | null): string => {
    return price !== null 
      ? new Intl.NumberFormat('ja-JP').format(price) + '円'
      : '未定';
  };
  ```
- **注意点**:
  - 落札価格は`history`配列内の各エントリの`sold_price`フィールドに格納
  - 最新の落札価格を取得する際は、必ず`history`配列の最後の要素を参照
  ```typescript
  // 最新の落札価格を取得
  const getLatestSoldPrice = (horse: Horse): number | null => {
    if (!horse.history || horse.history.length === 0) return null;
    return horse.history[horse.history.length - 1].sold_price;
  };
  ```

#### 2. 賞金情報（total_prize_*）
- **保存形式**: 万円単位の浮動小数点数（例: `9077.9`）
- **表示形式**: 数値 + 万円（例: `9,077.9万円`）
- **TypeScript型**: `number`
- **フィールド説明**:
  - `total_prize_start`: オークション時点の総賞金（一覧ページから取得）
  - `total_prize_latest`: 最新の総賞金（JBISから取得）
  - 初期状態では両方の値は同じ
- **フォーマット例**:
  ```typescript
  const formatPrize = (prize: number): string => {
    return new Intl.NumberFormat('ja-JP', { 
      minimumFractionDigits: 1,
      maximumFractionDigits: 1 
    }).format(prize) + '万円';
  };
  ```

#### 3. RIO（Return on Investment）
- **計算式**: 
  ```
  RIO = (落札後に稼いだ賞金総額) ÷ 落札価格
  ```
  - 落札後に稼いだ賞金総額 = `現在の総賞金 - オークション時の総賞金`
- **表示形式**: パーセンテージ（例: `15.0%`）
- **計算例**:
  ```typescript
  const calculateRIO = (horse: Horse): number => {
    const soldPrice = getLatestSoldPrice(horse);
    if (!soldPrice || soldPrice <= 0) return 0;
    
    const earnedPrize = (horse.total_prize_latest || 0) - (horse.total_prize_start || 0);
    return (earnedPrize * 10000) / soldPrice; // 万円→円に変換して計算
  };
  
  const formatRIO = (rio: number): string => {
    return (rio * 100).toFixed(1) + '%';
  };
  ```

#### 4. 日付・時刻
- **データベース形式**: `YYYY-MM-DD HH:MM:SS` (UTC)
- **フロントエンド表示**: `YYYY年MM月DD日`
- **変換例**:
  ```typescript
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    }).format(date);
  };
  ```

## ⏰ スケジュール

### 自動実行タスク
| タスク名 | スケジュール | 説明 |
|---------|------------|------|
| 通常スクレイピング | 木・日 23:59 (JST) | 楽天オークションから最新情報を取得 |
| オークション開催日スクレイピング | オークション開催日 20:00 (JST) | 落札価格情報を取得 |
| 賞金情報更新 | 毎月1日 02:00 (JST) | JBISから最新の賞金情報を取得 |
| データバックアップ | 毎日 04:00 (JST) | データベースのバックアップをS3に保存 |
| メンテナンス | 毎週月曜日 05:00 (JST) | ログローテーション、一時ファイル削除 |

## 🔍 デバッグガイド

### 1. スクレイピングのデバッグ

#### 1.1 テストモードでの実行
```bash
# バックエンドディレクトリで実行
python -m scripts.scraper --test
```

#### 1.2 特定の馬の情報を取得
```bash
# 馬IDを指定して実行
python -m scripts.scraper --horse-id 12345
```

### 2. フロントエンドのデバッグ

#### 2.1 開発サーバーの起動
```bash
# フロントエンドディレクトリで実行
pnpm dev
```

#### 2.2 テストの実行
```bash
# ユニットテスト
pnpm test

# E2Eテスト
pnpm test:e2e
```

### 3. バックエンドのデバッグ

#### 3.1 APIドキュメントの確認
http://localhost:8000/docs でSwagger UIが利用可能

#### 3.2 テストの実行
```bash
# バックエンドディレクトリで実行
pytest

# カバレッジレポート付きで実行
pytest --cov=app --cov-report=html
```

## 🛠 トラブルシューティング

### 1. スクレイピングが失敗する場合

#### 1.1 サイト構造の変更
**対応手順**:
1. 対象サイトのHTMLを確認
2. セレクターを更新
3. テストモードで動作確認

#### 1.2 レート制限に引っかかった場合
**対応手順**:
1. スクリプトを一時停止
2. 数分待機してから再開
3. 必要に応じて`--delay`オプションで遅延を増やす

### 2. フロントエンドが起動しない場合

#### 2.1 依存関係の問題
```bash
# 依存関係を再インストール
rm -rf node_modules
pnpm install
```

#### 2.2 ポートが使用中の場合
```bash
# 3000番ポートを使用しているプロセスを確認
lsof -i :3000

# プロセスを終了
kill -9 <PID>
```

## 📈 パフォーマンスチューニング

### 1. データベースクエリの最適化
- 必要なカラムのみを選択
- インデックスの追加を検討
- N+1問題に注意

### 2. フロントエンドの最適化
- コンポーネントのメモ化
- コード分割の活用
- 画像の最適化

## 🔒 セキュリティガイドライン

### 1. 認証・認可
- APIキーは環境変数で管理
- 機密情報はリポジトリにコミットしない

### 2. データ保護
- 個人情報の取り扱いに注意
- 定期的なバックアップの取得

## 📚 参考資料

### 公式ドキュメント
- [Next.js ドキュメント](https://nextjs.org/docs)
- [FastAPI ドキュメント](https://fastapi.tiangolo.com/)
- [SQLAlchemy ドキュメント](https://docs.sqlalchemy.org/)

### 参考記事
- [BeautifulSoup チートシート](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [TypeScript ハンドブック](https://www.typescriptlang.org/ja/docs/handbook/)
- [Tailwind CSS ドキュメント](https://tailwindcss.com/docs)

## 🤝 コントリビューション

1. イシューを作成して作業内容を報告
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを開く

## 📄 ライセンス

このプロジェクトは [MIT ライセンス](LICENSE) で公開されています。
