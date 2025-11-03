import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { HorseWithCalculations } from '../types/horse';
import { formatPrice, formatWeight, calcROI } from '../utils/formatters';

interface UseHorseDataProps {
  initialData?: {
    horses: HorseWithCalculations[];
    last_updated: string;
    total_horses: number;
    average_price: number;
    average_growth_rate: number;
    horses_with_growth_data: number;
  };
}

export const useHorseData = ({ initialData }: UseHorseDataProps = {}) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // 状態管理
  const [horses, setHorses] = useState<HorseWithCalculations[]>(initialData?.horses || []);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<Error | null>(null);
  
  // フィルターとソートの状態
  const [searchTerm, setSearchTerm] = useState('');
  const [showType, setShowType] = useState<'all' | 'sold' | 'unsold' | 'roi' | 'value'>('all');
  const [sortKey, setSortKey] = useState<keyof HorseWithCalculations>('price');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // 前回のソート状態を保持するためのref
  const prevSortRef = useRef<{ sortKey: keyof HorseWithCalculations; sortOrder: 'asc' | 'desc' }>({ 
    sortKey: 'price' as keyof HorseWithCalculations, 
    sortOrder: 'desc' 
  });
  
  // ページネーションの状態
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // データ取得
  const fetchHorseData = useCallback(async () => {
    debugger; // デバッガーで一時停止
    console.log('=== fetchHorseData 開始 ===');
    console.log('現在のソート状態 - sortKey:', sortKey, 'sortOrder:', sortOrder);
    
    if (initialData) {
      console.log('初期データを使用するためスキップ');
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      // ソートパラメータをURLに追加
      const sortParam = (() => {
        if (sortKey === 'total_prize_latest') {
          return sortOrder === 'asc' ? 'total_prize_asc' : 'total_prize_desc';
        }
        if (sortKey === 'price') {
          return sortOrder === 'asc' ? 'price_asc' : 'price_desc';
        }
        if (sortKey === 'name') {
          return sortOrder === 'asc' ? 'name_asc' : 'name_desc';
        }
        return 'date_desc';
      })();
      
      console.log('生成された sortParam:', sortParam);
      
      // ソートパラメータをURLに追加
      const params = new URLSearchParams();
      params.append('sort', sortParam);
      
      // ページネーションパラメータを追加
      params.append('skip', ((currentPage - 1) * itemsPerPage).toString());
      params.append('limit', itemsPerPage.toString());
      
      const url = `/api/horses?${params.toString()}`;
      console.log('リクエストURL:', url);
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      const data = await response.json();
      console.log('fetchHorseData - Response data:', data); // デバッグ用
      setHorses(data.horses || []);
    } catch (err) {
      console.error('Error fetching horse data:', err);
      setError(err instanceof Error ? err : new Error('データの取得中にエラーが発生しました'));
    } finally {
      setLoading(false);
    }
  }, [initialData, sortKey, sortOrder, currentPage, itemsPerPage]);

  // コンポーネントマウント時とソート状態の変更時にデータを取得
  useEffect(() => {
    debugger; // デバッガーで一時停止
    console.log('=== useEffect 実行 ===');
    console.log('現在のソート状態 - sortKey:', sortKey, 'sortOrder:', sortOrder);
    console.log('前回のソート状態 - sortKey:', prevSortRef.current.sortKey, 'sortOrder:', prevSortRef.current.sortOrder);
    
    // ソート状態が実際に変更された場合のみfetchを実行
    if (prevSortRef.current.sortKey !== sortKey || prevSortRef.current.sortOrder !== sortOrder) {
      console.log('ソート状態が変更されました。データを再取得します...');
      if (!initialData || ['price', 'name', 'total_prize_latest'].includes(sortKey as string)) {
        fetchHorseData();
      } else {
        console.log('ソートキーがバックエンドソート対象外のため、フロントエンドでソートします');
      }
      // 前回のソート状態を更新
      prevSortRef.current = { sortKey, sortOrder };
    } else if (!initialData) {
      console.log('初期データがなく、ソート状態が変わっていないため、データを取得します');
      fetchHorseData();
    }
  }, [fetchHorseData, initialData, sortKey, sortOrder]);

  // フィルタリングされた馬のリストを計算
  const filteredHorses = useMemo(() => {
    return horses.filter(horse => {
      // 検索キーワードによるフィルタリング
      const matchesSearch = 
        !searchTerm || 
        horse.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.sire?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.dam?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.dam_sire?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.seller?.toLowerCase().includes(searchTerm.toLowerCase());
      
      // 表示タイプによるフィルタリング
      const matchesType = 
        showType === 'all' ||
        (showType === 'sold' && horse.sold_price && !horse.is_unsold) ||
        (showType === 'unsold' && horse.is_unsold) ||
        (showType === 'roi' && horse.roi && horse.roi > 100) ||
        (showType === 'value' && horse.price_per_kg && horse.price_per_kg < 100);
      
      return matchesSearch && matchesType;
    });
  }, [horses, searchTerm, showType]);

  // ソートされた馬のリストを計算
  const sortedHorses = useMemo(() => {
    // バックエンドでソート済みの場合はそのまま返す
    if (['price_desc', 'price_asc', 'name_asc', 'name_desc'].includes(sortKey as string)) {
      return filteredHorses;
    }
    
    // フロントエンドでソートする場合
    return [...filteredHorses].sort((a, b) => {
      let aValue = a[sortKey];
      let bValue = b[sortKey];
      
      // ソートキーに基づいて値を比較
      if (aValue === undefined || aValue === null) return sortOrder === 'asc' ? -1 : 1;
      if (bValue === undefined || bValue === null) return sortOrder === 'asc' ? 1 : -1;
      
      // 文字列の場合は大文字小文字を区別せずに比較
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }
      
      if (aValue < bValue) return sortOrder === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
  }, [filteredHorses, sortKey, sortOrder]);

  // ページネーション
  const totalPages = Math.ceil(sortedHorses.length / itemsPerPage);
  const paginatedHorses = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedHorses.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedHorses, currentPage, itemsPerPage]);

  // ソートを変更する関数
  const handleSort = useCallback((key: keyof HorseWithCalculations) => {
    debugger; // デバッガーで一時停止
    console.log('=== handleSort 呼び出し ===');
    console.log('クリックされたキー:', key);
    console.log('現在の sortKey:', sortKey, 'sortOrder:', sortOrder);
    
    // 新しいソート順を決定（現在のキーと同じ場合はトグル、異なる場合は降順で開始）
    const newSortOrder = sortKey === key 
      ? sortOrder === 'asc' ? 'desc' : 'asc'
      : 'desc';
    
    console.log('新しい sortKey:', key, '新しい sortOrder:', newSortOrder);
    
    // 状態を更新
    console.log('状態を更新します...');
    setSortKey(key);
    setSortOrder(newSortOrder);
    setCurrentPage(1);
    
    // バックエンドでソートする必要がある場合
    const isBackendSort = ['price', 'name', 'total_prize_latest'].includes(key as string);
    
    if (isBackendSort) {
      console.log('バックエンドでソートを実行します');
      // 状態更新後にfetchHorseDataを実行
      setTimeout(() => {
        console.log('setTimeout 内で fetchHorseData を実行します');
        fetchHorseData();
      }, 0);
    } else if (key === 'total_prize_latest') {
      // フロントエンドでソートする場合（例：総賞金）
      console.log('フロントエンドでソートを実行します');
      setHorses(prevHorses => {
        console.log('前の馬データ:', prevHorses.length, '件');
        const sorted = [...prevHorses].sort((a, b) => {
          const aValue = a.total_prize_latest || 0;
          const bValue = b.total_prize_latest || 0;
          return newSortOrder === 'asc' ? aValue - bValue : bValue - aValue;
        });
        console.log('ソート後のデータ:', sorted.length, '件');
        return sorted;
      });
    }
  }, [sortKey, sortOrder, fetchHorseData]);

  // ページ変更ハンドラー
  const handlePageChange = useCallback((page: number) => {
    setCurrentPage(page);
    // ページの上部にスクロール
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, []);

  // 検索ハンドラー
  const handleSearch = useCallback((term: string) => {
    setSearchTerm(term);
    setCurrentPage(1); // 検索時に1ページ目に戻る
  }, []);

  // 表示タイプ変更ハンドラー
  const handleShowTypeChange = useCallback((type: 'all' | 'sold' | 'unsold' | 'roi' | 'value') => {
    setShowType(type);
    setCurrentPage(1); // フィルター変更時に1ページ目に戻る
  }, []);

  // 馬の詳細ページに遷移
  const navigateToHorseDetail = useCallback((horseId: string | number) => {
    router.push(`/horses/${horseId}`);
  }, [router]);

  // メタデータ
  const metadata = {
    last_updated: initialData?.last_updated || new Date().toISOString(),
    total_horses: initialData?.total_horses || 0,
    average_price: initialData?.average_price || 0,
    average_growth_rate: initialData?.average_growth_rate || 0,
    horses_with_growth_data: initialData?.horses_with_growth_data || 0,
  };

  return {
    // 状態
    horses: paginatedHorses,
    loading,
    error,
    
    // フィルターとソートの状態
    searchTerm,
    showType,
    sortKey,
    sortOrder,
    
    // ページネーションの状態
    currentPage,
    itemsPerPage,
    totalPages,
    totalHorses: filteredHorses.length,
    
    // メタデータ
    metadata,
    
    // ハンドラー
    handleSort,
    handlePageChange,
    handleSearch,
    handleShowTypeChange,
    navigateToHorseDetail,
    
    // ユーティリティ関数
    formatPrice,
    formatWeight,
    calcROI,
    
    // 生データ（必要に応じて）
    allHorses: horses,
  };
};
