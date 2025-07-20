# サラオクDB AI用クイックリファレンス

## 🚀 プロジェクト概要
- **目的**: 楽天サラブレッドオークション分析ツール
- **URL**: https://saraoku-db.vercel.app/
- **技術**: Next.js + FastAPI + SQLite
- **運用**: GitHub Actions + Vercel（無料）

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
- **価格**: 円単位（カンマ区切り）
- **賞金**: 万円単位（小数点1桁）
- **成長率**: 0.0%形式で統一
- **日付**: ISO 8601形式

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