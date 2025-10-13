'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import styles from './page.module.css';
import { formatPrizeMan } from '../../utils/format';
import { fetchHorsesList } from '../../utils/horseApi';
import { getDisplayPrice } from '../../utils/price';
import { Horse as UHorse, AuctionHistory as UHistory, ImageUrl } from '../../types/horse';
import { filterHorsesByTerm, sortHorses } from '../../utils/searchSort';
import { normalizeImageUrl } from '../../utils/url';

// seller が配列やJSON配列文字列のケースを正規化して日本語テキストを返す
function parseSeller(value: any): string {
  try {
    if (Array.isArray(value)) {
      return value.length > 0 ? String(value[0] ?? '') : '';
    }
    if (typeof value === 'string') {
      let str: any = value.trim();
      for (let i = 0; i < 2; i++) {
        const startsLikeJson = str.startsWith('[') || str.startsWith('{') || str.startsWith('"');
        if (!startsLikeJson) break;
        try {
          const parsed = JSON.parse(str);
          if (Array.isArray(parsed)) {
            return parsed.length > 0 ? String(parsed[0] ?? '') : '';
          }
          if (typeof parsed === 'string') {
            str = parsed.trim();
            continue;
          }
          break;
        } catch {
          break;
        }
      }
      return str;
    }
  } catch {
    return typeof value === 'string' ? value : '';
  }
  return '';
}

// 型は共通定義をベースにしつつ、このページで扱う拡張フィールドを許容
interface HorseListRow {
  // 必須フィールド
  id: string | number;
  horse_id?: number;  // APIからのレスポンスに合わせて追加
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire?: string;   // 念のため両方のケースに対応
  dam_sire?: string;  // バックエンドのレスポンスに合わせて追加
  
  // 画像関連（正規化後は常に文字列）
  image_url: string;
  primary_image?: string | null;
  
  // URL関連
  jbis_url: string;
  auction_url?: string;
  detail_url?: string;
  
  // オークション情報
  auction_date?: string | null;
  sold_price: number | null;
  is_unsold?: boolean;
  unsold?: boolean;
  seller?: string;
  weight?: number | null;
  
  // 賞金関連
  total_prize_latest?: number;
  total_prize_start?: number;
  prize_money?: { [key: string]: any };
  
  // その他の情報
  disease_tags?: string[] | string;
  comment?: string;
  race_record?: string | null;
  unsold_count?: number;
  
  // タイムスタンプ
  created_at?: string;
  updated_at?: string;
  
  // その他のフィールド
  [key: string]: any;
}

interface Metadata {
  last_updated?: string;
  total_horses?: number;
  total_auction_records?: number;
  [key: string]: any; // その他のプロパティも許容
}

interface HorseData {
  horses: HorseListRow[];
  auction_histories?: any[];  // バックエンドのレスポンスに合わせて追加
  auctionHistories: any[];    // 既存のプロパティも維持
  metadata: Metadata;
  [key: string]: any;  // その他のプロパティも許容
}

// 初期値（空データ）
const defaultHorseData: HorseData = {
  horses: [],
  auctionHistories: [],
  auction_histories: [],
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

    console.log('=== データ取得を開始します (utils/horseApi 経由) ===');
    setLoading(true);
    setError(null);
    
    try {
      console.log('fetchHorsesList を呼び出します...');
      const response = await fetchHorsesList();
      console.log('fetchHorsesList のレスポンス:', response);
      
      // レスポンスからhorsesとauctionHistoriesを取得
      const { horses = [], auctionHistories = [], metadata = {} } = response || {};
      
      console.log('取得したデータ:', {
        horsesCount: horses?.length || 0,
        auctionHistoriesCount: auctionHistories?.length || 0,
        metadata
      });
      
      // 馬データを正規化
      const normalizedHorses = (horses || []).map((horse: any) => ({
        ...horse,
        // idがなくてhorse_idがある場合は、horse_idをidとして使用
        id: horse.id || horse.horse_id,
        // 必須フィールドのデフォルト値を設定
        name: horse.name || `馬名不明 (ID: ${horse.id || horse.horse_id || '不明'})`,
        sex: horse.sex || '不明',
        age: horse.age || 0,
        sire: horse.sire || '不明',
        dam: horse.dam || '不明',
        damsire: horse.damsire || horse.dam_sire || '不明',
        jbis_url: horse.jbis_url || '',
        sold_price: horse.sold_price !== undefined ? horse.sold_price : null,
        is_unsold: horse.is_unsold || horse.unsold || false,
        image_url: typeof horse.image_url === 'string' 
          ? horse.image_url 
          : (horse.image_url?.image_url || '')
      }));
      
      // メタデータを安全に取得するヘルパー関数
      const getMetadataValue = <T extends keyof Metadata>(
        key: T, 
        defaultValue: Metadata[T]
      ): Metadata[T] => {
        if (metadata && typeof metadata === 'object' && key in metadata) {
          return (metadata as any)[key] || defaultValue;
        }
        return defaultValue;
      };

      // メタデータを正規化
      const normalizedMetadata: Metadata = {
        last_updated: getMetadataValue('last_updated', new Date().toISOString()),
        total_horses: getMetadataValue('total_horses', normalizedHorses.length),
        total_auction_records: getMetadataValue('total_auction_records', auctionHistories?.length || 0),
        ...(metadata || {}) // 他のメタデータプロパティも保持
      };
      
      // データを状態にセット
      setData({
        horses: normalizedHorses,
        auctionHistories: auctionHistories || [],
        metadata: normalizedMetadata
      });
      
      console.log('データをセットしました:', { 
        horsesCount: normalizedHorses.length,
        auctionHistoriesCount: auctionHistories?.length || 0,
        metadata: metadata
      });
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラー';
      console.error('データ取得エラー:', { error: err, errorMessage });
      setError(`データの取得中にエラーが発生しました: ${errorMessage}`);
      
      // エラー時に空のデータをセット
      setData({
        horses: [],
        auctionHistories: [],
        metadata: {
          last_updated: new Date().toISOString(),
          total_horses: 0,
          total_auction_records: 0,
        },
      });
    } finally {
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

      // 画像URLの正規化（相対→絶対URL）
      const rawImage = typeof horse.image_url === 'string'
        ? horse.image_url
        : ((horse.image_url as ImageUrl | null)?.image_url ?? '');
      const imageUrl = normalizeImageUrl(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001', rawImage || '');

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
        seller: parseSeller(latestAuction?.seller ?? horse.seller ?? '不明') || '不明',
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
    const filtered = filterHorsesByTerm(horsesWithAuctionInfo, searchTerm);
    const sorted = sortHorses(filtered, sortBy, sortOrder);
    return sorted;
  }, [horsesWithAuctionInfo, searchTerm, sortBy, sortOrder]);

  // 検索とソート処理は既にuseMemoで実装済み

  // 賞金表示は utils/format の共通関数を利用（UIは不変）

  // 価格表示は utils/price の仕様化ロジックを使用（UIは不変）

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
              {filteredHorses.map((horse: HorseListRow) => (
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
                      {getDisplayPrice({
                        unsold: horse.is_unsold,
                        sold_price: horse.sold_price,
                        history: (data.auctionHistories?.filter((ah: UHistory) => ah.horse_id === horse.id) || []) 
                      })}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {parseSeller(horse.seller) || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatPrizeMan(horse.total_prize_latest)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <pre className="bg-gray-50 p-4 rounded overflow-auto text-xs">
            {JSON.stringify(filteredHorses, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}