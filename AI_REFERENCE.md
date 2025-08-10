# サラオクDB AI用クイックリファレンス

## 🚀 プロジェクト概要

### 基本情報
- **プロジェクト名**: サラオクDB
- **目的**: 楽天サラブレッドオークションのデータを収集・分析するツール
- **本番URL**: [https://saraoku-db.vercel.app/](https://saraoku-db.vercel.app/)
- **開発URL**: http://localhost:3000
- **最終更新**: 2025年8月11日

### 技術スタック
- **フロントエンド**: Next.js 15.3.5 (App Router), TypeScript, Tailwind CSS
- **バックエンド**: FastAPI, Python 3.11
- **データベース**: SQLite
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
static-frontend/
├── src/app/                    # App Router ベースのページ
│   ├── (dashboard)             # ダッシュボード関連
│   ├── (marketing)             # マーケティングページ
│   ├── api/                    # APIルート
│   ├── horses/                 # 馬関連ページ
│   │   ├── [id]/               # 馬詳細 (動的ルート)
│   │   │   └── page.tsx        # 馬詳細ページ
│   │   └── page.tsx            # 馬一覧ページ
│   ├── layout.tsx              # ルートレイアウト
│   └── page.tsx                # ホームページ
├── components/                 # 再利用可能なコンポーネント
│   ├── ui/                     # shadcn/ui コンポーネント
│   ├── horses/                 # 馬関連コンポーネント
│   │   ├── HorseCard.tsx       # 馬カード
│   │   ├── HorseFilters.tsx    # フィルターコンポーネント
│   │   └── HorseStats.tsx      # 統計情報
│   └── shared/                 # 共通コンポーネント
└── lib/                        # ユーティリティ関数
    ├── api.ts                  # APIクライアント
    └── utils.ts                # ユーティリティ関数
```

### バックエンド (FastAPI)
```
backend/
├── app/
│   ├── api/                   # APIエンドポイント
│   │   ├── v1/                # APIバージョン1
│   │   │   ├── horses.py      # 馬関連API
│   │   │   └── auctions.py    # オークション関連API
│   ├── core/                  # コア機能
│   │   ├── config.py          # 設定
│   │   └── security.py        # 認証・認可
│   ├── db/                    # データベース関連
│   │   ├── models.py          # SQLAlchemyモデル
│   │   └── crud.py            # データベース操作
│   ├── services/              # ビジネスロジック
│   │   ├── scraper.py         # スクレイピングサービス
│   │   └── analyzer.py        # 分析サービス
│   └── main.py                # アプリケーションエントリーポイント
├── scrapers/                  # スクレイピングスクリプト
│   ├── rakuten_scraper.py     # 楽天オークションスクレイパー
│   └── jbis_scraper.py        # JBISスクレイパー
└── tests/                     # テスト
    ├── unit/                  # ユニットテスト
    └── integration/           # 統合テスト
```

### データファイル
```
static-frontend/public/data/
├── horses.json           # 基本馬データ
└── horses_history.json   # 履歴付きデータ（フロントエンド用）

data/
├── horses.db             # SQLiteデータベース
└── migrations/           # データベースマイグレーション
```

### GitHub Actions ワークフロー
```
.github/workflows/
├── deploy.yml            # 本番環境デプロイ
├── test.yml              # テスト自動化
├── scrape.yml            # 通常スクレイピング（木・日23:59）
├── scrape-auction.yml    # オークション開催日スクレイピング
└── scrape-jbis.yml       # 賞金情報更新（毎月1日03:00）
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

#### 5. 性別・年齢
- **性別**: `'牡' | '牝' | 'セ'`
- **年齢**: 数値（例: `3`）
- **表示例**: `3歳牡`

#### 6. 血統情報
- **保存形式**: 文字列
- **例**: 
  - 父: `キタサンブラック`
  - 母: `ウインドインハーヘア`
  - 母の父: `サンデーサイレンス`

## ⏰ スケジュール

### 自動実行タスク
| タスク名 | スケジュール | 説明 |
|---------|------------|------|
| 通常スクレイピング | 木・日 23:59 (JST) | 楽天オークションから最新情報を取得 |
| 賞金情報更新 | 毎月1日 02:00 (JST) | JBISから最新の賞金情報を取得 |
| データバックアップ | 毎日 03:00 (JST) | データベースのバックアップを取得 |

### タイトル形式
- 基本形式: `サラオクDB | [ページ名]`
- 例: 
  - `サラオクDB | 馬一覧`
  - `サラオクDB | サクラバクシンオー 詳細`

## 🔒 セキュリティ

### 基本方針
- 検索エンジンのインデックスを禁止（noindex, nofollow）
- robots.txtで全クローラーを禁止
- 機密情報は環境変数で管理
- パスワードはハッシュ化して保存

### セキュリティヘッダー
- Content-Security-Policy (CSP) の適切な設定
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- X-XSS-Protection: 1; mode=block
- Strict-Transport-Security の有効化

### レート制限
- APIエンドポイントにはレート制限を適用
- 1分間に60リクエストまで（デフォルト）
- 認証済みユーザーは制限を緩和

## 🧪 テストモードとキャッシュ

### テストモード

#### 有効化方法
```bash
# テストモードで実行（キャッシュ使用）
python improved_scraper.py --test

# テストモード + データベースに保存
python improved_scraper.py --test --save

# テストモード + 強制再取得
python improved_scraper.py --test --force
```

#### 動作仕様
1. **バリデーション**
   - 必須フィールドのチェックをスキップ
   - データの整合性チェックを簡略化

2. **キャッシュの使用**
   - `html_cache/` ディレクトリからHTMLを読み込み
   - 詳細ページのキャッシュが存在しない馬はスキップ
   - キャッシュの有効期限: 7日間

3. **データ保存**
   - デフォルトではデータベースに保存されない
   - `--save` フラグを指定した場合のみ保存
   - 保存前のプレビューが表示される

### キャッシュの仕組み

#### キャッシュディレクトリ構造
```
scripts/html_cache/
├── auction_lists/          # 一覧ページのキャッシュ
│   ├── auction_list_20250810.html
│   └── auction_list_20250813.html
├── horse_details/          # 馬詳細ページのキャッシュ
│   ├── horse_detail_サクラバクシンオー.html
│   └── horse_detail_キタサンブラック.html
└── jbis_pages/             # JBISページのキャッシュ
    ├── jbis_12345678.html  # 馬IDごとにキャッシュ
    └── jbis_87654321.html
```

#### キャッシュの管理
| コマンドラインオプション | 説明 |
|------------------------|------|
| `--test` | テストモード（キャッシュ使用） |
| `--force` | キャッシュを無視して再取得 |
| `--save` | データベースに保存 |
| `--cache-dir PATH` | カスタムキャッシュディレクトリ指定 |
| `--clear-cache` | キャッシュをクリア |

#### キャッシュの有効期限
| キャッシュタイプ | 有効期限 | 更新間隔 |
|----------------|---------|---------|
| 一覧ページ | 24時間 | オークション開催日のみ更新 |
| 馬詳細ページ | 7日間 | 初回取得時のみ |
| JBISページ | 30日間 | 賞金情報更新時のみ |

### デバッグ情報

#### ログレベル
| レベル | 説明 | 出力内容 |
|-------|------|---------|
| DEBUG | 詳細なデバッグ情報 | リクエスト/レスポンス、パース処理の詳細 |
| INFO | 通常の情報 | 処理の開始/終了、重要な状態変化 |
| WARNING | 警告 | 処理の続行は可能な問題 |
| ERROR | エラー | 処理の継続が不可能な問題 |

#### デバッグオプション
```bash
# デバッグログを有効化
python improved_scraper.py --debug

# ログレベルを指定
python improved_scraper.py --log-level DEBUG

# ログをファイルに出力
python improved_scraper.py --log-file debug.log
```

#### デバッグ出力例
```
[DEBUG] キャッシュから読み込み: auction_list_20250810.html
[INFO] 馬の一覧を取得しました: 45件
[DEBUG] 馬詳細の取得を開始: サクラバクシンオー
[WARNING] キャッシュが見つかりません: horse_detail_サクラバクシンオー.html
[INFO] 馬詳細を取得中: https://example.com/horse/123
[DEBUG] レスポンスステータス: 200
[ERROR] データのパースに失敗: 賞金情報が見つかりません
```

## 🐛 トラブルシューティングガイド

### 1. ビルドエラー

#### 1.1 `useEffect in Server Component` エラー
**問題**: サーバーコンポーネントで`useEffect`を使用している
**解決策**:
```tsx
// コンポーネントの先頭に追加
'use client';

import { useEffect } from 'react';

export default function ClientComponent() {
  useEffect(() => {
    // クライアントサイドの処理
  }, []);
  
  return <div>Client Component</div>;
}
```

#### 1.2 TypeScript型エラー
**問題**: 型定義が一致しない
**解決策**: 型アサーションを使用
```typescript
// 例: レスポンスデータの型アサーション
const data = await response.json() as HorseData;

// オプショナルチェーンで安全にアクセス
const sireName = horse.sire?.name;
```

#### 1.3 依存関係の問題
**問題**: パッケージのバージョン不一致
**解決策**:
```bash
# 依存関係を再インストール
rm -rf node_modules package-lock.json
pnpm install  # または npm install

# 特定のパッケージを再インストール
pnpm add package-name@latest
```

### 2. データ不整合

#### 2.1 成長率が正しく表示されない
**確認ポイント**:
1. `getGrowthRate`関数の計算ロジック
2. 賞金データの取得元（`total_prize_start`と`total_prize_latest`）
3. 0除算のハンドリング

**デバッグ例**:
```typescript
// デバッグ用のログを追加
console.log('開始賞金:', horse.total_prize_start);
console.log('最新賞金:', horse.total_prize_latest);
console.log('成長率:', getGrowthRate(horse));
```

#### 2.2 疾病タグが正しく抽出されない
**確認ポイント**:
1. `_extract_disease_tags`関数の正規表現
2. ソースHTMLの構造変更
3. タグのマッピング定義

**デバッグ例**:
```python
def _extract_disease_tags(html: str) -> List[str]:
    """疾病タグを抽出する"""
    soup = BeautifulSoup(html, 'html.parser')
    # デバッグ用にHTMLを出力
    print("=== 疾病タグ抽出元HTML ===")
    print(soup.prettify()[:500])  # 最初の500文字を表示
    # ... 抽出処理 ...
```

### 3. スクレイピング関連

#### 3.1 サイト構造の変更
**対応手順**:
1. 対象サイトのHTMLを確認
2. セレクターを更新
3. テストモードで動作確認

**例**:
```python
# 旧セレクター
# price = soup.select_one('.price')

# 新セレクター
price = soup.select_one('.new-price-selector')
```

#### 3.2 ネットワークエラー
**リトライ処理の実装例**:
```python
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def fetch_with_retry(url: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=30.0)
        response.raise_for_status()
        return response.text
```

#### 3.3 レート制限
**対策**:
```python
import asyncio

class RateLimiter:
    def __init__(self, calls_per_second: float = 1.0):
        self.calls_per_second = calls_per_second
        self.last_call = 0

    async def wait(self):
        now = asyncio.get_event_loop().time()
        elapsed = now - self.last_call
        wait_time = max(0, (1.0 / self.calls_per_second) - elapsed)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        self.last_call = asyncio.get_event_loop().time()

# 使用例
limiter = RateLimiter(calls_per_second=0.5)  # 1秒に0.5リクエスト

async def fetch_data(url: str):
    await limiter.wait()
    # リクエスト実行
    return await fetch_with_retry(url)
```

### 4. パフォーマンス問題

#### 4.1 データベースの遅延
**最適化ポイント**:
1. インデックスの追加
2. N+1クエリの解消
3. ページネーションの実装

**例**:
```python
# 非効率なクエリ
horses = session.query(Horse).all()
for horse in horses:
    print(horse.owner.name)  # N+1問題発生

# 最適化されたクエリ
from sqlalchemy.orm import joinedload
horses = session.query(Horse).options(joinedload(Horse.owner)).all()
for horse in horses:
    print(horse.owner.name)  # 事前にロード済み
```

#### 4.2 フロントエンドのパフォーマンス
**最適化ポイント**:
1. コンポーネントのメモ化
2. 不要な再レンダリングの防止
3. コード分割の適用

**例**:
```tsx
import { memo, useCallback } from 'react';

// メモ化されたコンポーネント
const HorseCard = memo(({ horse, onClick }) => {
  // コールバックのメモ化
  const handleClick = useCallback(() => {
    onClick(horse.id);
  }, [horse.id, onClick]);

  return (
    <div onClick={handleClick}>
      <h3>{horse.name}</h3>
      {/* その他の表示 */}
    </div>
  );
});

// プロパティの比較関数
HorseCard.propTypes = {
  horse: PropTypes.object.isRequired,
  onClick: PropTypes.func.isRequired,
};

// カスタム比較関数
HorseCard.defaultProps = {
  areEqual: (prevProps, nextProps) => {
    return prevProps.horse.id === nextProps.horse.id &&
           prevProps.onClick === nextProps.onClick;
  }
};

export default HorseCard;
```

## 📊 データ構造リファレンス

### 馬データ (Horse)

#### データベーススキーマ (horsesテーブル)

| フィールド名 | 型 | 説明 | 必須 | 例 |
|-------------|----|------|------|-----|
| id | Integer | 一意の識別子 | はい | 1 |
| name | String | 馬名 | はい | サクラバクシンオー |
| sex | Text | 性別（JSON配列） | はい | `["牡", "牡"]` |
| age | Text | 年齢（JSON配列） | はい | `[3, 4]` |
| sire | String | 父 | いいえ | ディープインパクト |
| dam | String | 母 | いいえ | ウインドインハーヘア |
| dam_sire | String | 母の父 | いいえ | サンデーサイレンス |
| race_record | String | 通算成績 | いいえ | 10-5-3-2 |
| weight | Integer | 馬体重（kg） | いいえ | 480 |
| total_prize_start | Float | 初出走時賞金（万円、小数点1桁） | いいえ | 0.0 |
| total_prize_latest | Float | 最新賞金（万円、小数点1桁） | いいえ | 1250.5 |
| sold_price | Text | 落札価格（JSON配列、円、カンマなし） | いいえ | `[10000000, 12000000]` |
| auction_date | Text | オークション日（JSON配列） | いいえ | `["2023-01-15", "2023-07-20"]` |
| seller | Text | 販売者（JSON配列） | いいえ | `["社台", "ノーザンファーム"]` |
| disease_tags | Text | 疾病タグ（カンマ区切り） | いいえ | `"骨折, 屈腱炎"` |
| comment | Text | コメント（JSON配列） | いいえ | `["初回コメント", "2回目コメント"]` |
| image_url | String | 画像URL | いいえ | https://example.com/image.jpg |
| primary_image | String | メイン画像URL | いいえ | https://example.com/primary.jpg |
| unsold_count | Integer | 主取り回数 | いいえ | 1 |
| created_at | DateTime | 作成日時 | はい | 2023-01-01 12:00:00 |
| updated_at | DateTime | 更新日時 | はい | 2023-01-01 12:00:00 |

#### フロントエンド型定義 (TypeScript)

```typescript
interface Horse {
  id: number;                      // 一意の識別子
  name: string;                    // 馬名
  sex: string | string[];          // 性別
  age: number | number[] | string | string[];  // 年齢
  color?: string;                  // 毛色
  birthday?: string;               // 生年月日 (YYYY-MM-DD)
  history: HorseHistory[];         // 履歴情報
  sire?: string;                   // 父
  dam?: string;                    // 母
  dam_sire?: string;               // 母の父
  primary_image?: string;          // メイン画像URL
  disease_tags?: string[];         // 疾病タグ
  jbis_url?: string;               // JBIS URL
  weight: number | null;           // 馬体重 (kg)
  unsold_count: number | null;     // 主取り回数
  total_prize_latest: number;      // 最新賞金 (万円、例: 10.0)
  created_at: string;              // 作成日時 (YYYY-MM-DD)
  updated_at: string;              // 更新日時 (YYYY-MM-DD)
  unsold?: boolean;                // 主取りフラグ
  seller?: string;                 // 販売者
  sold_price?: number | null;      // 落札価格 (円、例: 10000000)
  auction_date?: string;           // オークション日 (YYYY-MM-DD)
  detail_url?: string;             // 詳細ページURL
  total_prize_start?: number;      // 初出走時賞金 (万円、例: 0.0)
}

interface HorseHistory {
  date: string;          // 日付 (YYYY-MM-DD)
  event: string;         // イベント名
  price?: number;        // 価格（円、例: 10000000）
  weight?: number;       // 馬体重（kg）
  comment?: string;      // コメント
  seller?: string;       // 販売者
  auction_date?: string; // オークション日 (YYYY-MM-DD)
  disease_tags?: string[]; // 疾病タグ
}
```

## 📝 開発時の注意点

### フロントエンド
- **Next.js App Router**: サーバー/クライアントコンポーネント区別
- **TypeScript**: 厳密な型定義
- **Tailwind CSS**: ユーティリティファースト

### バックエンド
- **SQLite**: ファイルベースDB
- **FastAPI**: 非同期処理
- **スクレイピング**: エラーハンドリング重要

### データフロー
1. スクレイピング → SQLite
2. SQLite → JSON変換
3. JSON → フロントエンド表示

## 🎯 機能追加時の手順

1. **バックエンド**: スクレイピング・サービス追加
2. **データ変換**: JSON構造更新
3. **フロントエンド**: UI・ロジック追加
4. **テスト**: 手動動作確認
5. **デプロイ**: GitHubプッシュ

## 📞 緊急時対応

### スクレイピング停止
- GitHub Actions無効化
- バックエンドスケジューラー停止

### データ復旧
- `horses.json`手動更新
- データベース再構築

### デプロイ失敗
- Vercel設定確認
- ビルドログ確認

---

**更新**: 2025-07-20
**用途**: AI支援開発用 