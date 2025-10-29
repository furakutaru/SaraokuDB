'use client';

import React, { useState, useCallback, useMemo, lazy, Suspense } from 'react';
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
import { AuctionHistory } from '../../src/types/horse';
import { ja } from 'date-fns/locale';
import HeaderCard from './[id]/components/HeaderCard';

// 型定義をインポート
import type { Horse, SortableField } from './types';

// HorseData インターフェースを拡張して auction_histories に null を許容
interface HorseData {
  horses: Horse[];
  auction_histories?: (any | null)[];
  metadata?: {
    last_updated: string;
    total_horses: number;
    total_auction_records: number;
  };
}
import { useEffect } from 'react';

// コンポーネントの型定義をインポート
import type { ButtonProps } from './types/components/Button.types';
import type { HorseImageProps } from './types/components/HorseImage.types';

// カスタムフックをインポート
import { useHorsesData } from './hooks/useHorsesData';
import { useSorting } from './hooks/useSorting';
import { useFilters } from './hooks/useFilters';

// ユーティリティ関数をインポート
import { 
  isUnsoldHorse,
  formatSeller,
  getDisplayPrice,
  formatPrize,
  getGrowthRate
} from './utils/formatters';
import { formatAge } from './utils/formatAge';
import { parseDate } from './utils/dateUtils';
import SexBadge from './components/SexBadge';
import FilterControls from './components/FilterControls';

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
const Button = lazy(async () => {
  try {
    const mod = await import('@/components/ui/button');
    // 型アサーションを使用して互換性を確保
    return { default: mod.Button as React.ComponentType<React.PropsWithChildren<ButtonProps>> };
  } catch (error) {
    console.error('Failed to load Button component:', error);
    const FallbackButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
      ({ children, className = '', ...props }, ref) => (
        <button 
          ref={ref}
          className={`px-4 py-2 rounded ${className}`} 
          {...props}
        >
          {children}
        </button>
      )
    );
    FallbackButton.displayName = 'FallbackButton';
    return { default: FallbackButton };
  }
});

// HorseImage コンポーネントの動的インポート
const HorseImage = lazy(() => 
  import('@/components/HorseImage')
    .then(mod => ({ default: mod.default }))
    .catch(() => ({
      default: function FallbackHorseImage({ src, alt = 'Horse image', className = '', ...props }: HorseImageProps) {
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
      }
    }))
);

// Badge コンポーネントは使用しないためコメントアウト
// import { Badge } from "@/components/ui/badge";

// コンポーネントの型定義は types/index.ts からインポート済み

// ユーティリティ関数は utils/formatters.ts からインポート済み

// API関数は api/horsesApi.ts からインポート済み

// ユーティリティ関数は utils/formatters.ts からインポート済み

// コンポーネントをインポート
import HorseCard from './components/HorseCard/HorseCard';
import SortControls from './components/SortControls';
import SearchBar from './components/SearchBar';

// 型定義は types/index.ts からインポート済み


// ローディング中のスケルトンコンポーネント
const LoadingSkeleton = () => (
  <div className="space-y-4">
    {[...Array(5)].map((_, i) => (
      <div key={i} className="animate-pulse bg-gray-200 h-24 rounded-lg" />
    ))}
  </div>
);

// エラー表示コンポーネント
const ErrorDisplay = ({ error, onRetry }: { error: any, onRetry: () => void }) => {
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
            onClick={onRetry}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            再読み込み
          </button>
        </div>
      </div>
    </div>
  );
};

// データなし表示コンポーネント
const NoDataDisplay = ({ onReload }: { onReload: () => void }) => (
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
                onClick={onReload}
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

export default function HorsesPage() {
  // 1. すべてのフックを最初に呼び出す
  const router = useRouter();
  const { horses, loading, error, refreshData } = useHorsesData({ latestAuction: true });
  
  // 2. 状態管理
  const [showFilters, setShowFilters] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedHorse, setSelectedHorse] = useState<Horse | null>(null);
  const [showModal, setShowModal] = useState(false);
  
  // 3. フィルター状態を管理
  const { 
    filteredHorses = [], 
    filters = {
      searchQuery: '',
      sexFilter: 'all',
      priceRange: [0, 10000],
      ageRange: [0, 30],
      showUnsoldOnly: false,
    }, 
    updateFilters,
  } = useFilters(horses || [], {
    searchQuery: '',
    sexFilter: 'all',
    priceRange: [0, 10000],
    ageRange: [0, 30],
    showUnsoldOnly: false,
  });
  
  // 4. ソートを適用
  const sortingResult = useSorting(filteredHorses || []);
  const { 
    sortedHorses = [], 
    handleSort, 
    sortField = 'name', 
    sortOrder = 'asc' 
  } = sortingResult || {};
  
  // 5. 性別フィルターの状態を変換
  const sexFilter = useMemo(() => {
    if (filters.sexFilter === 'all') {
      return { male: true, female: true, gelding: true };
    }
    const selectedSexes = filters.sexFilter.split(',');
    return {
      male: selectedSexes.includes('牡'),
      female: selectedSexes.includes('牝'),
      gelding: selectedSexes.includes('セ')
    };
  }, [filters.sexFilter]);
  
  // 6. イベントハンドラー
  // 性別フィルターを更新
  const handleSexFilterChange = useCallback((filter: { male: boolean; female: boolean; gelding: boolean }) => {
    // 現在のフィルター状態を取得
    const currentFilter = filters.sexFilter;
    
    // 選択されている性別の配列を作成
    const selectedSexes = [];
    if (filter.male) selectedSexes.push('牡');
    if (filter.female) selectedSexes.push('牝');
    if (filter.gelding) selectedSexes.push('セ');

    // 選択された性別がない場合は'all'を設定
    if (selectedSexes.length === 0) {
      // 現在が'all'の場合は何もしない（無限ループ防止）
      if (currentFilter !== 'all') {
        updateFilters({ sexFilter: 'all' });
      }
    } 
    // すべての性別が選択されている場合は'all'を設定
    else if (selectedSexes.length === 3) {
      updateFilters({ sexFilter: 'all' });
    } 
    // 1つだけ選択されている場合はその性別を設定
    else if (selectedSexes.length === 1) {
      updateFilters({ sexFilter: selectedSexes[0] });
    } 
    // 2つ選択されている場合はカンマ区切りで設定
    else {
      updateFilters({ sexFilter: selectedSexes.join(',') });
    }
  }, [updateFilters]);
  
  // 性別フィルターの状態を更新（FilterControls 用）
  const handleSexFilterChangeWrapper = useCallback((newSexFilter: { male: boolean; female: boolean; gelding: boolean }) => {
    handleSexFilterChange(newSexFilter);
  }, [handleSexFilterChange]);
  
  // 個別の性別フィルターを更新
  const updateSexFilter = useCallback((sex: 'male' | 'female' | 'gelding', checked: boolean) => {
    const newSexFilter = { ...sexFilter, [sex]: checked };
    handleSexFilterChangeWrapper(newSexFilter);
  }, [sexFilter, handleSexFilterChangeWrapper]);
  
  // 年齢範囲を更新
  const handleAgeRangeChange = useCallback((newAgeRange: [number, number]) => {
    updateFilters({ ageRange: newAgeRange });
  }, [updateFilters]);

  // 検索クエリが変更されたときにフィルターを更新（即時更新）
  const handleSearchChange = useCallback((newSearchTerm: string) => {
    setSearchTerm(newSearchTerm);
    updateFilters({ searchQuery: newSearchTerm });
  }, [updateFilters]);

  // フィルターリセット時の処理
  const handleResetFilters = useCallback(() => {
    setSearchTerm('');
    updateFilters({ searchQuery: '' });
  }, [updateFilters]);

  // フィルターが変更されたときに検索バーの値を同期
  useEffect(() => {
    if (filters.searchQuery !== searchTerm) {
      setSearchTerm(filters.searchQuery);
    }
  }, [filters.searchQuery, searchTerm]);

  // ソートフィールドの変更を処理
  const handleSortFieldChange = useCallback((field: SortableField) => {
    handleSort(field);
  }, [handleSort]);

  // 7. ローディング中はスケルトンを表示
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <HeaderCard />
        <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
          <LoadingSkeleton />
        </main>
      </div>
    );
  }

  // 8. エラーが発生した場合はエラーを表示
  if (error) {
    return <ErrorDisplay error={error} onRetry={() => window.location.reload()} />;
  }

  // 9. データがない場合はメッセージを表示
  if (!horses || horses.length === 0) {
    return <NoDataDisplay onReload={() => window.location.reload()} />;
  }

  // 10. ユーティリティ関数
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

  // 性別フィルターに一致するかチェック
  const matchesSexFilter = (horse: any) => {
    if (filters.sexFilter === 'all') {
      return true;
    }
    
    const selectedSexes = filters.sexFilter.split(',');
    const horseSex = normalizeHorseSex(horse.sex);
    
    // デバッグ用ログ
    console.log('フィルター:', filters.sexFilter, 
                '選択された性別:', selectedSexes, 
                '元の性別:', horse.sex,
                '正規化後:', horseSex);
    
    // 馬の性別が選択された性別のいずれかに一致するか確認
    const matches = selectedSexes.some(sex => {
      const normalizedSex = sex.trim();
      // 馬の性別に選択された性別が含まれているか確認
      const match = horseSex.includes(normalizedSex);
      console.log('比較:', { normalizedSex, horseSex, match });
      return match;
    });
    
    console.log('マッチ結果:', matches);
    return matches;
  };
  
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
        <div className="mb-6 space-y-4">
          {/* 検索バーとフィルターボタン */}
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <SearchBar
                searchTerm={searchTerm}
                onSearchChange={handleSearchChange}
                placeholder="馬名、父、母、母父 で検索"
              />
            </div>
            <Button 
              variant="outline" 
              className="shrink-0"
              onClick={() => setShowFilters(!showFilters)}
            >
              {showFilters ? 'フィルターを隠す' : 'フィルターを表示'}
            </Button>
          </div>
          
          {/* フィルターコントロール */}
          {showFilters && (
          <div className="bg-gray-50 p-4 rounded-lg mb-6">
            <FilterControls
              sexFilter={sexFilter}
              onSexFilterChange={handleSexFilterChangeWrapper}
              ageRange={filters.ageRange}
              onAgeRangeChange={handleAgeRangeChange}
              onReset={handleResetFilters}
            />
          </div>
        )}  
        </div>

        {/* ソートコントロール */}
        <div className="px-4 sm:px-0 mb-4">
          <SortControls
            sortField={sortField}
            sortOrder={sortOrder}
            onSortFieldChange={handleSortFieldChange}
            onSortOrderChange={(order) => {
              // ソート順をトグルするために同じフィールドでソートをトリガー
              handleSort(sortField);
            }}
          />
        </div>

        {/* 馬一覧 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 px-4 sm:px-0">
          {(sortedHorses || []).map((horse, index) => (
            <HorseCard 
              key={horse.id}
              horse={{
                ...horse,
                // オークション履歴を使用
                auction_histories: horse.auction_histories || []
              }}
              onHorseClick={(horse) => {
                // 馬の詳細ページに遷移
                router.push(`/horses/${horse.id}`);
              }}
            />
          ))}
        </div>

        <div className="mt-8 text-center text-gray-600">
          {filteredHorses.length}頭の馬を表示中
        </div>
      </main>
    </div>
  );
}
