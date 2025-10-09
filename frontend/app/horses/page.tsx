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

// Button component type
type ButtonProps = {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  [key: string]: any;
};

let Button: React.FC<ButtonProps>;

try {
  const ButtonComponent = require("@/components/ui/button").Button;
  Button = ButtonComponent as React.FC<ButtonProps>;
} catch (e) {
  console.warn('Button component not found, using fallback');
  Button = ({ children, className = '', variant = 'default', ...props }: ButtonProps) => (
    <button 
      className={`px-4 py-2 rounded-md ${
        variant === 'destructive' 
          ? 'bg-red-600 hover:bg-red-700 text-white' 
          : 'bg-blue-600 hover:bg-blue-700 text-white'
      } ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

// HorseImage コンポーネントの型定義
type HorseImageProps = {
  src: string | { image_url: string } | null;
  alt?: string;
  className?: string;
  [key: string]: any;
};

// HorseImage コンポーネントの宣言
let HorseImage: React.ComponentType<HorseImageProps>;

try {
  HorseImage = require('@/components/HorseImage').default || (() => null);
} catch (e) {
  console.warn('HorseImage component not found, using fallback');
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

// 価格表示用のユーティリティ関数
const getDisplayPrice = (horse: any): string => {
  if (!horse) return '-';
  
  // 主取りフラグをチェック
  if (horse.is_unsold === true || horse.unsold === true) {
    return '主取り';
  }
  
  // 落札価格がある場合はそれを表示
  if (horse.sold_price !== undefined && horse.sold_price !== null) {
    // 文字列の場合は角括弧を削除
    const priceStr = String(horse.sold_price).replace(/[\[\]]/g, '');
    const price = Number(priceStr);
    
    if (!isNaN(price) && price > 0) {
      return `¥${price.toLocaleString()}`;
    }
  }
  
  // オークション履歴から最新の価格を取得
  if (horse.auction_histories && horse.auction_histories.length > 0) {
    const latestHistory = horse.auction_histories[0];
    if (latestHistory.sold_price !== undefined && latestHistory.sold_price !== null) {
      // 文字列の場合は角括弧を削除
      const priceStr = String(latestHistory.sold_price).replace(/[\[\]]/g, '');
      const price = Number(priceStr);
      
      if (!isNaN(price) && price > 0) {
        return `¥${price.toLocaleString()}`;
      }
    }
  }
  
  return '-';
};

// Badge コンポーネントは使用しないためコメントアウト
// import { Badge } from "@/components/ui/badge";

// コンポーネントの型定義
interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  auction_url: string;
  disease_tags: string[];
  weight: number | null;
  race_record: string;
  comment: string;
  created_at: string;
  updated_at: string;
  sold_price?: number | string | null;
  seller?: string;
  auction_date?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean | string;
  unsold?: boolean;
  auction_histories?: AuctionHistory[];
  [key: string]: any;
}

interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | string | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean | string;
  comment: string;
  created_at: string;
  [key: string]: any;
}

// 主取りフラグをチェックするヘルパー関数
const isUnsoldHorse = (horse: Horse): boolean => {
  return horse?.unsold === true || horse?.is_unsold === true;
};

// 価格を表示用にフォーマットする関数
const formatPrice = (price: any): string => {
  if (price === null || price === undefined) return '-';
  
  // 価格が配列の場合は最初の要素を使用
  if (Array.isArray(price) && price.length > 0) {
    price = price[0];
  }
  
  // 価格が文字列で角括弧で囲まれている場合（例: "[300000]"）を処理
  if (typeof price === 'string') {
    // 角括弧を除去
    if (price.startsWith('[') && price.endsWith(']')) {
      price = price.slice(1, -1);
    }
    
    // "null"の場合は主取りとして扱う
    if (price === 'null') {
      return '主取り';
    }
    
    // 数値に変換を試みる
    const numPrice = Number(price);
    
    // 有効な数値で0より大きい場合はフォーマットして返す
    if (!isNaN(numPrice) && numPrice > 0) {
      return `¥${numPrice.toLocaleString('ja-JP')}`;
    }
  } else if (typeof price === 'number' && price > 0) {
    // 数値で0より大きい場合はフォーマットして返す
    return `¥${price.toLocaleString('ja-JP')}`;
  }
  
  return '-';
};

// API functions
const fetchHorsesList = async (latestOnly: boolean = false): Promise<HorseData> => {
  try {
    console.log(`[fetchHorsesList] ${latestOnly ? '最新のオークションの馬' : '全ての馬'}を取得します...`);
    // URLSearchParams を使用してパラメータを正しくエンコード
    const params = new URLSearchParams();
    params.append('latest_auction', latestOnly ? 'true' : 'false');
    params.append('limit', '1000');
    params.append('skip', '0');
    
    console.log('[fetchHorsesList] リクエストパラメータ:', {
      latest_auction: latestOnly ? 'true' : 'false',
      url: `/api/horses?${params.toString()}`
    });
    
    const response = await fetch(`/api/horses?${params.toString()}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      },
      credentials: 'same-origin'
    });
    
    console.log('[fetchHorsesList] レスポンスステータス:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const responseData = await response.json();
    console.log('[fetchHorsesList] APIレスポンス:', {
      hasHorses: !!responseData.horses,
      horsesCount: responseData.horses?.length || 0,
      hasAuctionHistories: !!(responseData.auction_histories || responseData.auctionHistories),
      auctionHistoriesCount: (responseData.auction_histories || responseData.auctionHistories || []).length,
      metadata: responseData.metadata
    });

    // データの正規化
    const horses = Array.isArray(responseData.horses) ? responseData.horses : [];
    const auctionHistories = Array.isArray(responseData.auction_histories) 
      ? responseData.auction_histories 
      : (Array.isArray(responseData.auctionHistories) ? responseData.auctionHistories : []);

    return {
      horses,
      auctionHistories,
      metadata: {
        last_updated: responseData.metadata?.last_updated || new Date().toISOString(),
        total_horses: responseData.metadata?.total_horses || horses.length,
        total_auction_records: responseData.metadata?.total_auction_records || auctionHistories.length
      }
    };
  } catch (error) {
    console.error('[fetchHorsesList] エラーが発生しました:', error);
    // エラー時に空のデータを返す
    return {
      horses: [],
      auctionHistories: [],
      metadata: {
        last_updated: new Date().toISOString(),
        total_horses: 0,
        total_auction_records: 0
      }
    };
  }
};

// 性別と年齢を適切に表示するためのヘルパー関数
const formatAge = (sex: any, age: any): string => {
  // 性別の処理
  const getSexString = (s: any): string => {
    if (!s) return '';
    
    // 配列の場合は最初の要素を使用
    const sexValue = Array.isArray(s) ? s[0] : s;
    
    // 文字列に変換
    let sexStr = String(sexValue);
    
    // Unicodeエスケープシーケンスをデコード
    sexStr = sexStr.replace(/\\u([\dA-Fa-f]{4})/g, (_, p1) => {
      return String.fromCharCode(parseInt(p1, 16));
    });
    
    // 性別の正規化
    if (sexStr.includes('牡') || sexStr === '牡馬') return '牡';
    if (sexStr.includes('牝') || sexStr === '牝馬') return '牝';
    if (sexStr.includes('セ') || sexStr === 'せん' || sexStr === 'セン') return 'セ';
    
    return sexStr;
  };

  // 年齢の処理
  const getAgeString = (a: any): string => {
    if (a === null || a === undefined) return '';
    
    // 配列の場合は最初の要素を使用
    const ageValue = Array.isArray(a) ? a[0] : a;
    
    // 文字列に変換して数字のみを抽出
    const num = String(ageValue).replace(/\D/g, '');
    return num ? `${num}歳` : '';
  };

  const sexStr = getSexString(sex);
  const ageStr = getAgeString(age);
  
  return [sexStr, ageStr].filter(Boolean).join(' ');
};

// 売り主情報を適切に表示するためのヘルパー関数
const formatSeller = (seller: any): string => {
  if (!seller) return '不明';
  
  // 配列の場合は最初の要素を使用
  const sellerStr = Array.isArray(seller) ? seller[0] : seller;
  
  // 文字列に変換
  let result = String(sellerStr);
  
  // 不要な文字列を削除
  result = result
    .replace(/^\s*\[\s*'([^']*)'\s*\]\s*$/, '$1') // ['文字列'] の形式を削除
    .replace(/^\s*'([^']*)'\s*$/, '$1') // '文字列' の形式を削除
    .replace(/^\s*\["']?([^"'\]]*)["']?\s*\]\s*$/, '$1') // ["文字列"] の形式を削除
    .replace(/^\s*\{\s*\$\$hashKey\s*:\s*[^}]*\s*\}\s*$/, '') // {$$hashKey: ...} の形式を削除
    .trim();
  
  // 空文字列の場合は「不明」を返す
  return result || '不明';
};

interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  auction_url: string;
  disease_tags: string[];
  weight: number | null;
  race_record: string;
  comment: string;
  created_at: string;
  updated_at: string;
  sold_price?: number | string | null;
  seller?: string;
  auction_date?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean | string;
  unsold?: boolean;
}

interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | string | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean | string;
  unsold?: boolean;
  comment: string;
  created_at: string;
}

// Union type to handle both camelCase and snake_case property names
type AuctionHistories = any[] | undefined;

interface HorseData {
  horses: any[];
  // Support both camelCase and snake_case for API compatibility
  auctionHistories?: AuctionHistories;
  auction_histories?: AuctionHistories;
  metadata?: {
    last_updated?: string;
    total_horses?: number;
    total_auction_records?: number;
    [key: string]: any; // Allow additional metadata properties
  };
  [key: string]: any; // Allow additional properties
}

// プロパティ名に関わらずオークション履歴を取得するヘルパー関数
const getAuctionHistories = (data: HorseData | null): any[] => {
  if (!data) return [];
  // どちらのプロパティ名でも取得できるようにする
  return data.auctionHistories || data.auction_histories || [];
};

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
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center p-6 max-w-md mx-auto bg-white rounded-xl shadow-md">
          <div className="text-red-500 text-5xl mb-4">⚠️</div>
          <h2 className="text-xl font-semibold text-gray-800 mb-2">エラーが発生しました</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            再読み込み
          </button>
        </div>
      </div>
    );
  }

  if (!data || !data.horses || data.horses.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-600">表示するデータがありません</p>
        </div>
      </div>
    );
  }

  // フィルタリングとソート
  const filteredHorses = (data?.horses || [])
    .filter(horse => {
      if (!searchTerm) return true;
      if (!horse) return false;
      
      const term = searchTerm.toLowerCase();
      const name = String(horse.name || '').toLowerCase();
      const sire = String(horse.sire || '').toLowerCase();
      const dam = String(horse.dam || '').toLowerCase();
      const damsire = String(horse.damsire || '').toLowerCase();
      const seller = String(horse.seller || '').toLowerCase();
      
      // 病歴タグの処理
      const diseaseTags = Array.isArray(horse.disease_tags) 
        ? horse.disease_tags 
        : horse.disease_tags ? [horse.disease_tags] : [];
      
      const hasMatchingDiseaseTag = diseaseTags.some((tag: any) => 
        String(tag || '').toLowerCase().includes(term)
      );
      
      return (
        name.includes(term) ||
        sire.includes(term) ||
        dam.includes(term) ||
        damsire.includes(term) ||
        seller.includes(term) ||
        hasMatchingDiseaseTag
      );
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
                    <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                      {formatAge(horse.sex, horse.age)}
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
                    
                    <div className="grid grid-cols-2 gap-2 text-sm text-gray-700 mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{horse.sire} × {horse.dam}</span>
                          {horse.disease_tags && horse.disease_tags.length > 0 && (
                            <div className="border border-red-300 text-red-500 px-2 py-0.5 rounded text-xs">
                              {horse.disease_tags[0]}
                            </div>
                          )}
                        </div>
                        <div className="text-gray-500 text-xs">母父</div>
                        <div className="truncate">{horse.damsire || '不明'}</div>
                      </div>
                      <div>
                        <div className="text-gray-500 text-xs">売主</div>
                        <div className="truncate">{formatSeller(horse.seller)}</div>
                      </div>
                    </div>
                    
                    <div className="mt-auto pt-2 border-t border-gray-100">
                      <div className="flex justify-between items-center">
                        <span className={`inline-block px-2 py-1 text-xs rounded ${
                          horse.is_unsold
                            ? 'bg-gray-100 text-gray-800' 
                            : 'bg-blue-100 text-blue-800'
                        }`}>
                          {getDisplayPrice(horse) === '主取り' 
                            ? '主取り' 
                            : getDisplayPrice(horse) !== '-' 
                              ? getDisplayPrice(horse) 
                              : '価格未設定'}
                        </span>
                        
                        {horse.disease_tags && horse.disease_tags.length > 0 && (
                          <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-pink-800 bg-pink-100 rounded">
                            病歴: {horse.disease_tags[0]}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        {/* 結果件数 */}
        <div className="mt-8 text-center text-gray-600">
          {filteredHorses.length}頭の馬を表示中
        </div>
      </main>
    </div>
  );
}
