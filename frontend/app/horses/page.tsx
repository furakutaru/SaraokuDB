'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Modal, 
  Box, 
  Typography,
  Skeleton,
  Tooltip
} from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import HeaderCard from './[id]/components/HeaderCard';

// 型定義をインポート
import type { 
  Horse, 
  AuctionHistory, 
  HorseData, 
  SortOrder,
  SortableField
} from './types';

// コンポーネントの型定義をインポート
import type { ButtonProps } from './types/components/Button.types';
import type { HorseImageProps } from './types/components/HorseImage.types';

// HorseImage コンポーネントの動的インポート
import { 
  isUnsoldHorse,
  formatSeller,
  getDisplayPrice,
  formatPrize,
  getGrowthRate
} from './utils/formatters'; // utils/formatters.ts からインポート
import { formatAge } from './utils/formatAge';
import SexBadge from '@/app/horses/components/SexBadge';

// 性別データを正規化する関数
const normalizeHorseSex = (sex: any): string => {
  if (!sex) return '';
  
  try {
    // 文字列で、JSON配列の形式になっている場合
    if (typeof sex === 'string' && sex.startsWith('[')) {
      const parsed = JSON.parse(sex);
      if (Array.isArray(parsed) && parsed.length > 0) {
        // 配列の最初の要素を取得し、エスケープシーケンスを処理
        const firstItem = parsed[0];
        if (typeof firstItem === 'string') {
          // Unicodeエスケープシーケンスをデコード
          return firstItem.replace(/\\u([\dA-Fa-f]{4})/g, (match, p1) => {
            return String.fromCharCode(parseInt(p1, 16));
          });
        }
        return String(firstItem);
      }
    }
    // 配列の場合
    if (Array.isArray(sex) && sex.length > 0) {
      return String(sex[0]);
    }
    // その他の場合
    return String(sex);
  } catch (e) {
    console.error('性別データの正規化に失敗しました:', e, '元の値:', sex);
    return String(sex);
  }
};
// formatAge は別ファイルからインポート

// API関数をインポート
import { fetchHorsesList, getAuctionHistories } from './api/horsesApi';

// Button コンポーネントの動的インポート
let Button: React.FC<ButtonProps>;

try {
  const ButtonComponent = require("@/components/ui/button").Button;
  Button = ButtonComponent;
} catch (e) {
  // フォールバックのボタンコンポーネント
  Button = ({ children, className = '', variant = 'default', ...props }: ButtonProps) => {
    return (
      <button className={`px-4 py-2 rounded ${className}`} {...props}>
        {children}
      </button>
    );
  };
}

// HorseImage コンポーネントの動的インポート
let HorseImage: React.FC<HorseImageProps>;

try {
  const HorseImageComponent = require('@/components/HorseImage').default;
  HorseImage = HorseImageComponent;
} catch (e) {
  console.warn('HorseImage component not found, using fallback');
  // フォールバックのHorseImageコンポーネント
  HorseImage = ({ src, alt = 'Horse image', className = '', ...props }: HorseImageProps) => {
    const [imgSrc, setImgSrc] = React.useState<string>('');
    
    React.useEffect(() => {
      if (src) {
        setImgSrc(typeof src === 'string' ? src : src?.image_url || '');
      }
    }, [src]);

    return (
      <div className={`relative w-full aspect-[3/2] bg-gray-100 rounded-t-lg overflow-hidden ${className}`} {...props}>
        {imgSrc ? (
          <img 
            src={imgSrc}
            alt={alt}
            className="absolute inset-0 w-full h-full object-cover"
            width={300}
            height={200}
            onError={(e) => {
              // Fallback to a placeholder if image fails to load
              const target = e.target as HTMLImageElement;
              target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0idz0iNiIgaGVpZ2h0PSI2Ij48cGF0aCBkPSJNMTggMTNoMS42ODNjLjU1OSAwIC45NTItLjU4MS43ODctMS4xNDNsLTEuNjUxLTQuODU0YTEuNSAxLjUgMCAwIDAtMS40MDItMS4wNDNoLTguMzE0YTEuNSAxLjUgMCAwIDAtMS40MDIgMS4wNDNsLTEuNjUgNC44NTRjLS4xNjUuNTYyLjIyOCAxLjE0My43ODcgMS4xNDNIM2ExIDEgMCAwIDAtMSAxdjhhMSAxIDAgMCAwIDEgMWgxNGExIDEgMCAwIDAgMS0xdi04YTEgMSAwIDAgMC0xLTF6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 13h1.683c.559 0 .952-.581.787-1.143l-1.651-4.854a1.5 1.5 0 0 0-1.402-1.043h-8.314a1.5 1.5 0 0 0-1.402 1.043l-1.65 4.854c-.165.562.228 1.143.787 1.143H3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1z"></path>
              <circle cx="12" cy="10" r="3"></circle>
            </svg>
          </div>
        )}
      </div>
    );
  };
}

// Badge コンポーネントは使用しないためコメントアウト
// import { Badge } from "@/components/ui/badge";

// コンポーネントの型定義は types/index.ts からインポート済み

// ユーティリティ関数は utils/formatters.ts からインポート済み

// API関数は api/horsesApi.ts からインポート済み

// ユーティリティ関数は utils/formatters.ts からインポート済み

// 型定義は types/index.ts からインポート済み

export default function HorsesPage() {
  const router = useRouter();
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortField, setSortField] = useState<keyof Horse>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [selectedHorse, setSelectedHorse] = useState<Horse | null>(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log('[useEffect] データ取得を開始します...');
        
        // 現在のパスを取得（/horses または / の場合に最新のオークションの馬を表示）
        const isRecentPage = window.location.pathname === '/horses' || window.location.pathname === '/';
        
        console.log('[useEffect] 現在のパス:', {
          pathname: window.location.pathname,
          isRecentPage,
          search: window.location.search
        });
        
        // 最新のオークションの馬のみを取得するかどうかを決定
        const result = await fetchHorsesList(isRecentPage);
        const auctionHistories = result.auctionHistories || result.auction_histories || [];
        
        console.log('[useEffect] 取得したデータ:', {
          isRecentPage,
          horsesCount: result.horses.length,
          auctionHistoriesCount: auctionHistories.length,
          metadata: result.metadata
        });
        
        if (isMounted) {
          setData({
            horses: result.horses,
            auctionHistories,
            metadata: result.metadata
          });
        }
      } catch (err) {
        console.error('[useEffect] データ取得エラー:', err);
        if (isMounted) {
          setError(`データの取得中にエラーが発生しました: ${err instanceof Error ? err.message : String(err)}`);
          // エラー時も空のデータをセット
          setData({
            horses: [],
            auctionHistories: [],
            metadata: {
              last_updated: new Date().toISOString(),
              total_horses: 0,
              total_auction_records: 0
            }
          });
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchData();
    
    // Cleanup function to avoid state updates after unmount
    return () => {
      isMounted = false;
    };
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="spinner-border animate-spin inline-block w-8 h-8 border-4 rounded-full" role="status">
            <span className="sr-only">Loading...</span>
          </div>
          <p className="mt-2 text-gray-600">データを読み込んでいます...</p>
        </div>
      </div>
    );
  }

  if (error) {
    // エラーメッセージを安全に表示するための処理
    const safeErrorMessage = (error: any): string => {
      try {
        if (typeof error === 'string') return error;
        if (error && typeof error.message === 'string') return error.message;
        return '不明なエラーが発生しました';
      } catch (e) {
        return 'エラーメッセージの処理中にエラーが発生しました';
      }
    };

    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">エラーが発生しました</h2>
          <div className="text-gray-600 mb-4 overflow-auto max-h-40">
            <pre className="text-xs text-left whitespace-pre-wrap break-words">
              {safeErrorMessage(error)}
            </pre>
          </div>
          <div className="mt-4 space-x-2">
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              再読み込み
            </button>
            <button
              onClick={() => router.push('/')}
              className="px-4 py-2 bg-gray-200 text-gray-800 rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
            >
              トップに戻る
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!data || !data.horses || data.horses.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50">
        <HeaderCard />
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <div className="text-sm text-yellow-700">
                  <p>表示するデータがありません。</p>
                  <p className="mt-1">以下のいずれかの理由が考えられます：</p>
                  <ul className="list-disc list-inside mt-1 space-y-1 text-sm">
                    <li>検索条件に一致する馬がいません</li>
                    <li>データがまだ登録されていません</li>
                    <li>APIからのデータ取得に失敗しました</li>
                  </ul>
                </div>
                <div className="mt-3">
                  <button
                    onClick={() => window.location.reload()}
                    className="inline-flex items-center px-3 py-1.5 border border-transparent text-xs font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    再読み込み
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    );
  }

  // 文字列を安全に比較するヘルパー関数
  const safeStringCompare = (str1: any, str2: string): boolean => {
    try {
      const s1 = String(str1 || '').normalize('NFC').toLowerCase();
      const s2 = String(str2 || '').normalize('NFC').toLowerCase();
      return s1.includes(s2);
    } catch (e) {
      console.error('文字列比較エラー:', e);
      return false;
    }
  };

  // フィルタリングとソート
  const filteredHorses = (data?.horses || [])
    .filter(horse => {
      if (!searchTerm) return true;
      if (!horse) return false;
      
      const term = searchTerm.toLowerCase();
      
      // 各フィールドのnull/undefinedチェックと文字列化を安全に行う
      const name = String(horse.name || '');
      const sire = String(horse.sire || '');
      const dam = String(horse.dam || '');
      const damsire = String(horse.damsire || '');
      const seller = String(horse.seller || '');
      
      // 病歴タグの処理
      const diseaseTags = Array.isArray(horse.disease_tags) 
        ? horse.disease_tags 
        : horse.disease_tags ? [horse.disease_tags] : [];
      
      const hasMatchingDiseaseTag = diseaseTags.some((tag: any) => 
        String(tag || '').toLowerCase().includes(term)
      );
      
      try {
        return (
          safeStringCompare(name, term) ||
          safeStringCompare(sire, term) ||
          safeStringCompare(dam, term) ||
          safeStringCompare(damsire, term) ||
          safeStringCompare(seller, term) ||
          hasMatchingDiseaseTag
        );
      } catch (e) {
        console.error('フィルタリングエラー:', e, horse);
        return false;
      }
    })
    .sort((a, b) => {
      if (!a || !b) return 0;
      
      let comparison = 0;
      const aValue = a[sortField as keyof typeof a];
      const bValue = b[sortField as keyof typeof b];

      if (aValue === bValue) return 0;
      if (aValue === null || aValue === undefined) return sortOrder === 'asc' ? 1 : -1;
      if (bValue === null || bValue === undefined) return sortOrder === 'asc' ? -1 : 1;

      try {
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          comparison = aValue.localeCompare(bValue);
        } else if (typeof aValue === 'number' && typeof bValue === 'number') {
          comparison = aValue - bValue;
        } else if (aValue instanceof Date && bValue instanceof Date) {
          comparison = aValue.getTime() - bValue.getTime();
        } else {
          // 日付文字列の場合は日付として比較を試みる
          const aDate = new Date(String(aValue));
          const bDate = new Date(String(bValue));
          if (!isNaN(aDate.getTime()) && !isNaN(bDate.getTime())) {
            comparison = aDate.getTime() - bDate.getTime();
          } else {
            comparison = String(aValue).localeCompare(String(bValue));
          }
        }
      } catch (e) {
        console.error('Error during sort:', e);
        return 0;
      }

      return sortOrder === 'asc' ? comparison : -comparison;
    });

  // 賞金表示用関数
  // 賞金は万円単位で表示
  const formatPrize = (val: number | string | null | undefined) => {
    if (val === null || val === undefined || val === '' || isNaN(Number(val))) return '-';
    return `${Number(val).toFixed(1)}万円`;
  };

  const getGrowthRate = (start: number, latest: number) => {
    if (start === 0) return '0.0';
    return ((latest - start) / start * 100).toFixed(1);
  };

  // メインのレンダリング
  return (
    <div className="min-h-screen bg-gray-50">
      <HeaderCard />

      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {/* 検索バー */}
        <div className="px-4 sm:px-0 mb-6">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg className="h-5 w-5 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path fillRule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clipRule="evenodd" />
              </svg>
            </div>
            <input
              type="text"
              className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              placeholder="馬名、父、母、母父、売主、病歴 などで検索"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>

        {/* ソートコントロール */}
        <div className="px-4 sm:px-0 mb-4 flex items-center space-x-4">
          <div>
            <label htmlFor="sort-field" className="block text-sm font-medium text-gray-700 mb-1">
              並べ替え
            </label>
            <select
              id="sort-field"
              className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
              value={sortField}
              onChange={(e) => setSortField(e.target.value as keyof Horse)}
            >
              <option value="name">馬名</option>
              <option value="sold_price">落札価格</option>
              <option value="auction_date">オークション日</option>
              <option value="total_prize_latest">総賞金</option>
              <option value="age">年齢</option>
            </select>
          </div>
          <div className="mt-6">
            <button
              type="button"
              className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
            >
              {sortOrder === 'asc' ? '昇順' : '降順'}
              {sortOrder === 'asc' ? (
                <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* 馬一覧 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 px-4 sm:px-0">
          {filteredHorses.map((horse) => {
            const history = (data?.auctionHistories || []).filter((h: any) => h.horse_id === horse.id);
            const latestHistory = history[0];
            
            // デバッグ用: 馬のデータをログに出力
            console.log('Horse data:', {
              id: horse.id,
              name: horse.name,
              sold_price: horse.sold_price,
              is_unsold: horse.is_unsold,
              auctionHistories: history,
              latestHistory: latestHistory
            });
            
            return (
              <Link href={`/horses/${horse.id}`} key={horse.id} className="group">
                <div className="bg-white overflow-hidden shadow rounded-lg h-full flex flex-col hover:shadow-lg transition-shadow duration-200">
                  {/* 画像エリア */}
                  <div className="relative h-48 bg-gray-200 overflow-hidden">
                    <HorseImage 
                      src={horse.image_url} 
                      alt={horse.name}
                      className="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105"
                    />
                    <div className="absolute top-2 right-2">
                      <SexBadge sex={normalizeHorseSex(horse.sex)} age={horse.age} className="text-xs" />
                    </div>
                    {horse.disease_tags && horse.disease_tags.length > 0 && (
                      <div className="absolute top-2 left-2">
                        <div className="bg-red-100 text-red-800 text-xs px-2 py-1 rounded">
                          病歴: {horse.disease_tags[0]}
                          {horse.disease_tags.length > 1 && ` +${horse.disease_tags.length - 1}`}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 馬情報エリア */}
                  <div className="p-4 flex-1 flex flex-col">
                    <div className="mb-2">
                      <h3 className="text-lg font-semibold">{horse.name}</h3>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm text-gray-700 mb-3">
                      <div className="text-gray-600 space-y-1">
                        <div className="flex">
                          <span className="w-12 flex-shrink-0">父</span>
                          <span className="truncate">{horse.sire || '不明'}</span>
                        </div>
                        <div className="flex">
                          <span className="w-12 flex-shrink-0">母</span>
                          <span className="truncate">{horse.dam || '不明'}</span>
                        </div>
                        <div className="flex">
                          <span className="w-12 flex-shrink-0">母父</span>
                          <span className="truncate">{horse.damsire || '不明'}</span>
                        </div>
                      </div>
                      <div className="text-gray-600 border-l border-gray-200 pl-4">
                        <div className="text-sm text-gray-500 mb-1">販売者</div>
                        <div className="font-medium truncate">{latestHistory?.seller || '不明'}</div>
                      </div>
                      <div className="mt-2">
                        {isUnsoldHorse(horse) 
                          ? <span className="text-red-600 font-medium">主取り</span>
                          : getDisplayPrice(horse) !== '-' 
                            ? getDisplayPrice(horse) 
                            : '価格未設定'}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="mt-8 text-center text-gray-600">
          {filteredHorses.length}頭の馬を表示中
        </div>
      </main>
    </div>
  );
}
