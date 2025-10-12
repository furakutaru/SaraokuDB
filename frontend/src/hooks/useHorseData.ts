import { useState, useEffect, useCallback, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { AnalysisHorse } from '../types/horse';
import { formatPrice, formatWeight, calcROI } from '../utils/formatters';

interface UseHorseDataProps {
  initialData?: {
    horses: AnalysisHorse[];
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
  const [horses, setHorses] = useState<AnalysisHorse[]>(initialData?.horses || []);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState<Error | null>(null);
  
  // フィルターとソートの状態
  const [searchTerm, setSearchTerm] = useState('');
  const [showType, setShowType] = useState<'all' | 'sold' | 'unsold' | 'roi' | 'value'>('all');
  const [sortKey, setSortKey] = useState<keyof AnalysisHorse>('sort_price');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  // ページネーションの状態
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 20;

  // データ取得
  const fetchHorseData = useCallback(async () => {
    if (initialData) return; // 初期データがある場合は再取得しない
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/horses');
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      const data = await response.json();
      setHorses(data.horses || []);
    } catch (err) {
      console.error('Error fetching horse data:', err);
      setError(err instanceof Error ? err : new Error('データの取得中にエラーが発生しました'));
    } finally {
      setLoading(false);
    }
  }, [initialData]);

  // コンポーネントマウント時にデータを取得
  useEffect(() => {
    if (!initialData) {
      fetchHorseData();
    }
  }, [fetchHorseData, initialData]);

  // フィルタリングされた馬のリストを計算
  const filteredHorses = useMemo(() => {
    return horses.filter(horse => {
      // 検索キーワードによるフィルタリング
      const matchesSearch = 
        !searchTerm || 
        horse.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.sire?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.dam?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        horse.damsire?.toLowerCase().includes(searchTerm.toLowerCase()) ||
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

  // ソートハンドラー
  const handleSort = useCallback((key: keyof AnalysisHorse) => {
    if (sortKey === key) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
    setCurrentPage(1); // ソート時に1ページ目に戻る
  }, [sortKey]);

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
