'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import styles from './page.module.css';

// 型定義
interface Horse {
  id: number;
  auction_id?: string | null;
  name: string;
  sex?: string | null;
  age?: number | null;
  sire?: string | null;
  dam?: string | null;
  damsire?: string | null;
  race_record?: string | null;
  weight?: number | null;
  total_prize_start?: number | null;
  total_prize_latest?: number | null;
  sold_price?: any; // JSON文字列または配列の可能性
  auction_date?: string | null;
  seller?: string | null;
  disease_tags?: string | string[] | null;
  comment?: string | null;
  image_url?: string | null;
  primary_image?: string | null;
  unsold_count?: number;
  is_unsold?: boolean;
  jbis_url?: string;
  auction_url?: string;
  created_at: string;
  updated_at: string;
}

interface AuctionHistory {
  id: number;
  horse_id: number;
  auction_date: string | null;
  sold_price: any; // JSON文字列または配列の可能性
  total_prize_start: number | null;
  total_prize_latest: number | null;
  weight: number | null;
  seller: string | null;
  is_unsold: boolean;
  comment: string | null;
  created_at: string;
}

interface Metadata {
  last_updated: string;
  total_horses: number;
  total_auction_records: number;
}

interface HorseData {
  horses: Horse[];
  auctionHistories: AuctionHistory[];
  metadata: Metadata;
}

// デフォルトの馬データ
const defaultHorseData: HorseData = {
  horses: [],
  auctionHistories: [],
  metadata: {
    last_updated: new Date().toISOString(),
    total_horses: 0,
    total_auction_records: 0
  }
};

// 検索とソート用の型
type SortField = 'name' | 'age' | 'auction_date' | 'sold_price' | 'total_prize_latest';
type SortOrder = 'asc' | 'desc';

export default function HorsesPage() {
  const router = useRouter();
  const [data, setData] = useState<HorseData>(defaultHorseData);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [sortBy, setSortBy] = useState<SortField>('auction_date');
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc');
  const [mounted, setMounted] = useState(false);

  // コンポーネントのマウント状態を設定
  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  const fetchData = useCallback(async () => {
    if (!mounted) return;
    
    console.log('=== データ取得を開始します ===');
    setLoading(true);
    setError(null);
    
    try {
      // 環境変数からAPIのベースURLを取得
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
      // backend/routers/horses.py は APIRouter(prefix="/api") のため /api/horses が正しい
      const apiUrl = `${apiBaseUrl}/api/horses`;
      
      console.log('APIリクエスト先:', apiUrl);
      
      // キャッシュを無効化
      const timestamp = new Date().getTime();
      const urlWithCacheBuster = `${apiUrl}?_=${timestamp}`;
      
      const startTime = Date.now();
      const response = await fetch(urlWithCacheBuster, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
          'Expires': '0'
        },
        cache: 'no-store',
        credentials: 'same-origin'
      });

      const responseTime = Date.now() - startTime;
      console.log(`APIレスポンス受信 (${responseTime}ms)`, {
        status: response.status,
        statusText: response.statusText
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('APIエラーレスポンス:', {
          status: response.status,
          statusText: response.statusText,
          body: errorText
        });
        throw new Error(`HTTPエラー! ステータス: ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('JSON以外のレスポンスを受信:', text);
        throw new Error('無効なレスポンス形式です');
      }
      
      const responseData = await response.json();
      console.log('APIレスポンスデータ:', responseData);
      
      // データを正規化
      const horsesData = responseData.horses || [];
      const auctionHistories = responseData.auctionHistories || [];
      
      if (horsesData.length > 0) {
        console.log('最初の馬のデータ:', JSON.stringify(horsesData[0], null, 2));
      }
      
      // 馬データにオークション履歴をマージ
      const horsesWithAuctionData = horsesData.map((horse: Horse) => {
        const horseHistory = auctionHistories.find((h: AuctionHistory) => h.horse_id === horse.id);
        return {
          ...horse,
          is_unsold: (horse.unsold_count || 0) > 0,
          jbis_url: horse.image_url, // 一時的にimage_urlをjbis_urlとして使用
          auction_url: `#${horse.id}`, // 一時的にIDを使用
          ...(horseHistory || {})
        } as Horse & { is_unsold: boolean; jbis_url?: string; auction_url: string };
      });
      
      setData({
        horses: horsesWithAuctionData,
        auctionHistories,
        metadata: responseData.metadata || {
          last_updated: new Date().toISOString(),
          total_horses: horsesData.length,
          total_auction_records: auctionHistories.length
        }
      });
      
      setLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      console.error('データ取得エラー:', { error: err, errorMessage });
      setError(`データの取得中にエラーが発生しました: ${errorMessage}`);
      setLoading(false);
    }
  }, [mounted]);

  useEffect(() => {
    console.log('useEffectが実行されました');
    fetchData();
  }, [fetchData]);

  // ローディング中の表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-4">
        <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-blue-500 mb-4"></div>
        <p className="text-gray-600 text-lg">データを読み込み中...</p>
        <div className="mt-6 p-4 bg-white rounded-lg shadow-md max-w-2xl w-full">
          <h2 className="text-lg font-semibold mb-3">デバッグ情報</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="font-medium">API エンドポイント:</p>
              <p className="break-all bg-gray-50 p-2 rounded mt-1">
                {process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'}/api/horses
              </p>
            </div>
            <div>
              <p className="font-medium">環境:</p>
              <p className="bg-gray-50 p-2 rounded mt-1">{process.env.NODE_ENV}</p>
            </div>
            <div>
              <p className="font-medium">最終更新:</p>
              <p className="bg-gray-50 p-2 rounded mt-1">
                {new Date().toLocaleString('ja-JP')}
              </p>
            </div>
            <div>
              <p className="font-medium">ステータス:</p>
              <p className="bg-yellow-50 text-yellow-800 p-2 rounded mt-1">
                データ取得中...
              </p>
            </div>
          </div>
          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
            <p className="text-blue-800 text-sm">
              ブラウザの開発者ツール（F12）を開き、コンソールタブで詳細なログを確認できます。
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    console.error('Error:', { error, data });
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">直近の追加</h1>
                <p className="text-gray-600">直近1週間以内に追加された馬の一覧です。</p>
              </div>
              <div className="text-sm text-gray-500">
                現在の日時: {new Date().toLocaleString('ja-JP')}
              </div>
            </div>
            <p className="text-red-600 mb-4">{error}</p>
            <button 
              onClick={() => {
                setLoading(true);
                setError(null);
                fetchData();
              }} 
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              再試行
            </button>
          </div>
        </div>
      </div>
    );
  }

  // 馬データとオークション履歴を結合
  const horsesWithAuctionInfo = useMemo(() => {
    console.log('horsesWithAuctionInfo - データの状態:', {
      hasHorses: !!data.horses,
      horsesCount: data.horses?.length || 0,
      hasAuctionHistories: !!data.auctionHistories,
      auctionHistoriesCount: data.auctionHistories?.length || 0
    });

    if (!data.horses || data.horses.length === 0) {
      console.warn('表示する馬のデータがありません');
      return [];
    }

    return data.horses.map(horse => {
      // 馬に関連するオークション履歴を取得
      const horseAuctions = data.auctionHistories?.filter(ah => ah.horse_id === horse.id) || [];
      
      // 最新のオークション履歴を取得
      const latestAuction = [...horseAuctions].sort((a, b) => {
        const dateA = a.auction_date ? new Date(a.auction_date).getTime() : 0;
        const dateB = b.auction_date ? new Date(b.auction_date).getTime() : 0;
        return dateB - dateA;
      })[0];

      // 馬オブジェクトのsold_priceを優先し、なければオークション履歴から取得
      const soldPrice = horse.sold_price !== undefined 
        ? horse.sold_price 
        : (latestAuction?.sold_price !== undefined ? latestAuction.sold_price : null);
      
      // 主取りかどうかを判定
      const isUnsold = horse.is_unsold !== undefined 
        ? horse.is_unsold 
        : (soldPrice === null || soldPrice === 0);

      // 画像URLが相対パスの場合に絶対URLに変換
      let imageUrl = horse.image_url || '';
      if (imageUrl && !imageUrl.startsWith('http') && !imageUrl.startsWith('data:')) {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        imageUrl = `${baseUrl}${imageUrl.startsWith('/') ? '' : '/'}${imageUrl}`;
      }

      return {
        ...horse,
        id: horse.id || `temp-${Math.random().toString(36).substr(2, 9)}`,
        name: horse.name || '名前不明',
        sex: horse.sex || '不明',
        age: horse.age || 0,
        sire: horse.sire || '不明',
        dam: horse.dam || '不明',
        damsire: horse.damsire || '不明',
        auction_date: latestAuction?.auction_date || horse.auction_date || '',
        sold_price: soldPrice,
        seller: latestAuction?.seller || horse.seller || '不明',
        is_unsold: isUnsold,
        total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start || 0,
        total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest || 0,
        weight: latestAuction?.weight || horse.weight || null,
        image_url: imageUrl,
        created_at: horse.created_at || new Date().toISOString(),
        updated_at: horse.updated_at || new Date().toISOString(),
        jbis_url: horse.jbis_url || '',
        auction_url: horse.auction_url || '',
        disease_tags: horse.disease_tags || [],
        race_record: horse.race_record || '',
        comment: horse.comment || ''
      };
    });
  }, [data.horses, data.auctionHistories]);

  // 検索とソート
  const filteredHorses = useMemo(() => {
    console.log('filteredHorses - フィルタリング前の馬の数:', horsesWithAuctionInfo.length);
    if (!horsesWithAuctionInfo.length) {
      console.warn('フィルタリング対象の馬データがありません');
      return [];
    }
    
    return [...horsesWithAuctionInfo]
      .filter(horse => {
        if (!horse) return false;
        const term = searchTerm.toLowerCase();
        return (
          horse.name.toLowerCase().includes(term) ||
          (horse.sire || '').toLowerCase().includes(term) ||
          (horse.dam || '').toLowerCase().includes(term) ||
          (horse.damsire || '').toLowerCase().includes(term) ||
          (horse.seller || '').toLowerCase().includes(term)
        );
      })
      .sort((a, b) => {
        let comparison = 0;
        switch (sortBy) {
          case 'name':
            comparison = a.name.localeCompare(b.name);
            break;
          case 'sold_price':
            comparison = (a.sold_price || 0) - (b.sold_price || 0);
            break;
          case 'age':
            comparison = (a.age || 0) - (b.age || 0);
            break;
          case 'auction_date':
            const dateA = a.auction_date ? new Date(a.auction_date).getTime() : 0;
            const dateB = b.auction_date ? new Date(b.auction_date).getTime() : 0;
            comparison = dateA - dateB;
            break;
          case 'total_prize_latest':
            comparison = (a.total_prize_latest || 0) - (b.total_prize_latest || 0);
            break;
        }
        return sortOrder === 'asc' ? comparison : -comparison;
      });
  }, [horsesWithAuctionInfo, searchTerm, sortBy, sortOrder]);

  // 検索とソート処理は既にuseMemoで実装済み

  // 賞金表示用関数
  // 賞金は万円単位で表示
  const formatPrize = (val: number | string | null | undefined) => {
    if (val === null || val === undefined || val === '' || isNaN(Number(val))) return '-';
    return `${Number(val).toFixed(1)}万円`;
  };

  // 落札価格表示用関数
  // 落札価格は取得値そのまま（円単位）で表示
  const displayPrice = (price: number | null | undefined, is_unsold: boolean | undefined) => {
    if (is_unsold === true) return '主取り';
    if (price === null || price === undefined) return '-';
    return '¥' + price.toLocaleString();
  };

  const getGrowthRate = (start: number, latest: number) => {
    if (start === 0) return '0.0';
    return ((latest - start) / start * 100).toFixed(1);
  };

  // デバッグ情報を表示
  console.log('レンダリング時の状態:', {
    loading,
    error,
    filteredHorsesCount: filteredHorses.length,
    searchTerm,
    sortBy,
    sortOrder,
    apiUrl: process.env.NEXT_PUBLIC_API_URL
  }, []);

  // マウント時にデータを取得
  useEffect(() => {
    if (!mounted) return;
    
    console.log('データ取得を開始します');
    fetchData().catch(error => {
      console.error('データ取得中にエラーが発生しました:', error);
    });
  }, [mounted, fetchData]);

  // ローディング状態をログに出力
  useEffect(() => {
    console.log('ローディング状態:', loading);
  }, [loading]);

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* デバッグ情報 */}
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-yellow-700">
              デバッグ情報: {filteredHorses.length} 頭の馬が表示中
              <br />
              API: {process.env.NEXT_PUBLIC_API_URL || 'デフォルトのAPI URLが使用されます'}
              <br />
              最終更新: {data.metadata?.last_updated || '不明'}
            </p>
          </div>
        </div>
      </div>
      <div className="max-w-7xl mx-auto">
        {/* ヘッダー */}
        <div className="mb-6">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold">馬一覧</h1>
            <button 
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              再読み込み
            </button>
          </div>
          <div className="flex justify-between items-center mt-4">
            <div className="flex space-x-2">
              <input
                type="text"
                placeholder="検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="px-3 py-1 border rounded"
              />
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as SortField)}
                className="px-3 py-1 border rounded"
              >
                <option value="name">馬名</option>
                <option value="sold_price">落札価格</option>
                <option value="age">年齢</option>
              </select>
              <select
                value={sortOrder}
                onChange={(e) => setSortOrder(e.target.value as 'asc' | 'desc')}
                className="px-3 py-1 border rounded"
              >
                <option value="asc">昇順</option>
                <option value="desc">降順</option>
              </select>
            </div>
            <div className="text-sm text-gray-600">
              {filteredHorses.length}頭の馬を表示中
            </div>
          </div>
        </div>

        {/* テーブル */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">馬名</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">性別・年齢</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">父</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">母</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">母父</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">落札価格</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">売主</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">賞金</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredHorses.map((horse) => (
                <tr key={horse.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-10 w-10">
                        {horse.image_url && (
                          <img className="h-10 w-10 rounded-full" src={horse.image_url} alt={horse.name} />
                        )}
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{horse.name}</div>
                        <div className="text-sm text-gray-500">{horse.comment || 'コメントなし'}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{horse.sex}</div>
                    <div className="text-sm text-gray-500">{horse.age}歳</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{horse.sire || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{horse.dam || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900">{horse.damsire || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      horse.is_unsold 
                        ? 'bg-gray-100 text-gray-800' 
                        : 'bg-green-100 text-green-800'
                    }`}>
                      {displayPrice(horse.sold_price, horse.is_unsold)}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {horse.seller || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatPrize(horse.total_prize_latest)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* JSON表示 */}
        <div className="mt-8 bg-white p-4 rounded-lg shadow">
          <h2 className="text-lg font-semibold mb-2">JSONデータ</h2>
          <pre className="bg-gray-50 p-4 rounded overflow-auto text-xs">
            {JSON.stringify(filteredHorses, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}