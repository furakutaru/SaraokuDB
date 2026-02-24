# APIキャッシュ実装ドキュメント

## 概要

無料枠環境でのパフォーマンス向上のため、Next.js APIルートにインメモリキャッシュを実装しました。

## 実装内容

### 1. キャッシュライブラリ (`/src/lib/cache.ts`)

- **MemoryCacheクラス**: インメモリキャッシュの実装
- **TTLサポート**: 各キャッシュエントリに有効期限を設定
- **自動クリーンアップ**: 5分ごとに古いキャッシュを自動削除
- **キャッシュ統計**: キャッシュの状態を監視する機能

```typescript
// 使用例
import { apiCache, generateCacheKey } from '@/lib/cache';

// キャッシュに保存
apiCache.set(key, data, 5 * 60 * 1000); // 5分TTL

// キャッシュから取得
const cached = apiCache.get(key);

// キャッシュキー生成
const cacheKey = generateCacheKey('/api/horses', { skip: 0, limit: 24 });
```

### 2. APIエンドポイントのキャッシュ化

#### `/api/horses` (馬一覧取得)
- **キャッシュ時間**: 5分
- **キャッシュキー**: `skip`, `limit`, `sort`, `latest_auction_only` パラメータ
- **対象**: ページネーションされた馬データ

#### `/api/horses/[id]` (馬詳細取得)
- **キャッシュ時間**: 10分
- **キャッシュキー**: 馬ID
- **対象**: 個別馬の詳細情報とオークション履歴

### 3. キャッシュ管理API (`/api/cache`)

#### GET /api/cache?action=stats
キャッシュの統計情報を取得
```json
{
  "cache_size": 15,
  "cache_keys": [
    "/api/horses?limit=24&skip=0&sort=price_desc&latest_auction_only=false",
    "/api/horses/12345"
  ],
  "timestamp": "2026-02-24T19:15:00.000Z"
}
```

#### GET /api/cache?action=clear
すべてのキャッシュをクリア
```json
{
  "message": "All cache cleared",
  "timestamp": "2026-02-24T19:15:00.000Z"
}
```

#### GET /api/cache?action=clear&key=/api/horses/12345
特定のキャッシュをクリア
```json
{
  "message": "Cache key '/api/horses/12345' deleted",
  "deleted": true,
  "timestamp": "2026-02-24T19:15:00.000Z"
}
```

#### GET /api/cache?action=cleanup
古いキャッシュを手動でクリーンアップ
```json
{
  "message": "Cache cleanup completed",
  "timestamp": "2026-02-24T19:15:00.000Z"
}
```

## パフォーマンス効果

### 期待される改善
1. **DBクエリ削減**: キャッシュヒット率70-80%でDBアクセスを大幅削減
2. **レスポンスタイム**: キャッシュヒット時の応答時間が10-50msに改善
3. **Neon負荷軽減**: 無料枠の接続数制限のリスクを低減
4. **Render負荷軽減**: CPU使用率の削減でスリープリスクを低減

### キャッシュ戦略
- **馬一覧**: 5分キャッシュ（頻繁にアクセスされるが、データ更新は少ない）
- **馬詳細**: 10分キャッシュ（個別データは変更頻度が低い）
- **自動クリーンアップ**: 5分ごとに古いエントリを削除

## 無料枠での運用

### Neon (PostgreSQL)
- **接続数削減**: キャッシュによりDB接続を70-80%削減見込み
- **クエリ実行時間**: キャッシュヒット時は0ms
- **ストレージ**: 影響なし

### Render (バックエンド)
- **CPU使用率**: DBアクセス削減でCPU負荷を軽減
- **メモリ使用**: キャッシュによりメモリ使用量は増加するが、無料枠の512MB以内に収まるよう調整
- **スリープ防止**: レスポンス速度向上でアクティブ状態を維持

### Vercel (フロントエンド)
- **関数実行時間**: キャッシュにより実行時間を短縮
- **帯域**: 変更なし（同じデータ量を転送）

## 監視と管理

### ログ監視
キャッシュのヒット/ミス状況はコンソールログで確認：
```
[API/Horses] Cache hit for /api/horses?limit=24&skip=0&sort=price_desc&latest_auction_only=false
[API/Horses] Cache miss, fetching from DB: skip=0, limit=24, sort=price_desc, latest=false
```

### キャッシュ統計
定期的にキャッシュ統計を確認して効果を測定：
```bash
curl "https://your-domain.vercel.app/api/cache?action=stats"
```

### 手動クリア
データ更新時はキャッシュを手動でクリア：
```bash
curl "https://your-domain.vercel.app/api/cache?action=clear"
```

## 今後の改善案

1. **Redis導入**: スケーラビリティ向上のため（有料プラン移行時）
2. **キャッシュ戦略の最適化**: データ更新頻度に応じたTTL調整
3. **CDNキャッシュ**: VercelのEdgeキャッシュと連携
4. **部分キャッシュ**: 大きなデータの一部のみキャッシュ

## 注意事項

- **メモリ制限**: Vercelの無料枠ではメモリに制限あり
- **キャッシュ無効化**: データ更新時は手動または自動でキャッシュクリアが必要
- **Cold Start**: デプロイ直後はキャッシュが空のため初回のみ遅延あり
