# サラオクDB AI用クイックリファレンス

## 🚀 プロジェクト概要
- **目的**: 楽天サラブレッドオークション分析ツール
- **URL**: https://saraoku-db.vercel.app/
- **技術**: Next.js + FastAPI + SQLite
- **運用**: GitHub Actions + Vercel（無料）
- **最終更新**: 2025-08-02

## 📁 重要なファイル・ディレクトリ

### フロントエンド（メイン）
```
static-frontend/src/app/
├── page.tsx              # ホームページ
├── layout.tsx            # レイアウト・メタデータ
├── horses/
│   ├── page.tsx          # 馬一覧
│   └── [id]/page.tsx     # 馬詳細
└── dashboard/page.tsx    # 解析ページ
```

### データファイル
```
static-frontend/public/data/
├── horses.json           # 基本データ
└── horses_history.json   # 履歴付きデータ（フロントエンド使用）
```

### バックエンド
```
backend/
├── scrapers/             # スクレイピング
├── services/             # ビジネスロジック
├── scheduler/            # 自動実行
└── database/             # DBモデル
```

### 自動化
```
.github/workflows/
├── scrape.yml            # メイン（木・日23:59）
├── scrape-auction.yml    # オークション（木・日23:59）
└── scrape-jbis.yml       # 賞金更新（毎月1日03:00）
```

## 🔧 重要な仕様

### データ形式
- **価格（落札価格など）**: 
  - 保存形式: 円単位の整数（例: `10000000`）
  - 表示形式: カンマ区切り + 円（例: `10,000,000円`）
  - コード: `new Intl.NumberFormat('ja-JP').format(price) + '円'`
  - **重要**: 落札価格は`history`配列内の各エントリの`sold_price`フィールドに格納されます。最新の落札価格を取得するには、`history`配列の最後の要素を参照してください。
    ```typescript
    // 最新の落札価格を取得する例
    const latestSoldPrice = horse.history.length > 0 ? horse.history[horse.history.length - 1].sold_price : null;
    ```
- **賞金（total_prize_*）**: 
  - 保存形式: 万円単位の浮動小数点数（小数点以下1桁、例: `10.0`）
  - 表示形式: 数値 + 万円（例: `10.0万円`）
- **RIO（Return on Investment）**:
  - 計算式: `RIO = (落札後に稼いだ賞金総額) ÷ 落札価格`
  - 落札後に稼いだ賞金総額: `現在の総賞金 - オークション時の総賞金`
  - 表示形式: パーセンテージ（例: `15.0%`）
  - コード例:
    ```typescript
    const earnedPrize = (horse.total_prize_latest || 0) - (horse.total_prize_start || 0);
    const rio = soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;
    const displayRIO = (rio * 100).toFixed(1) + '%';
    ```
- **成長率**: 0.0%形式で統一
- **日付**: 
  - データベース: `YYYY-MM-DD HH:MM:SS`
  - フロントエンド: `YYYY-MM-DD`

### スケジュール
- **オークション**: 木・日 23:59
- **賞金更新**: 毎月1日 02:00
- **タイトル**: `サラオクDB | [ページ名]`

### セキュリティ
- **検索エンジン**: 禁止（noindex, nofollow）
- **robots.txt**: 全クローラー禁止

## 🐛 よくある問題

### ビルドエラー
- **useEffect in Server Component**: `'use client'`追加
- **TypeScript型エラー**: 型定義確認
- **依存関係**: `npm install`実行

### データ不整合
- **成長率表示**: `getGrowthRate`関数確認
- **疾病タグ**: `_extract_disease_tags`確認
- **JSON形式**: 構造統一確認

### スクレイピング失敗
- **サイト構造変更**: セレクター更新
- **ネットワークエラー**: リトライ機能確認
- **重複実行**: スケジューラー確認

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