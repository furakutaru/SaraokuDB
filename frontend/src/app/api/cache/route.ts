import { NextResponse } from 'next/server';
import { apiCache } from '@/lib/cache';

// キャッシュ管理用API
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const action = searchParams.get('action');

  try {
    switch (action) {
      case 'stats':
        // キャッシュ統計を取得
        const stats = apiCache.getStats();
        return NextResponse.json({
          cache_size: stats.size,
          cache_keys: stats.keys,
          timestamp: new Date().toISOString()
        });

      case 'clear':
        // キャッシュをクリア
        const key = searchParams.get('key');
        if (key) {
          const deleted = apiCache.delete(key);
          return NextResponse.json({
            message: deleted ? `Cache key '${key}' deleted` : `Cache key '${key}' not found`,
            deleted,
            timestamp: new Date().toISOString()
          });
        } else {
          apiCache.clear();
          return NextResponse.json({
            message: 'All cache cleared',
            timestamp: new Date().toISOString()
          });
        }

      case 'cleanup':
        // 古いキャッシュをクリーンアップ
        apiCache.cleanup();
        return NextResponse.json({
          message: 'Cache cleanup completed',
          timestamp: new Date().toISOString()
        });

      default:
        return NextResponse.json({
          error: 'Invalid action. Use: stats, clear, or cleanup',
          available_actions: ['stats', 'clear', 'cleanup'],
          timestamp: new Date().toISOString()
        }, { status: 400 });
    }
  } catch (error) {
    console.error('[API/Cache] Error:', error);
    return NextResponse.json(
      { error: 'キャッシュ管理中にエラーが発生しました' },
      { status: 500 }
    );
  }
}
