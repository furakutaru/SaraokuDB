import { useState, useCallback } from 'react';
import { Horse } from '../types';
import { isUnsoldHorse } from '../utils/formatters';

type FilterOptions = {
  searchQuery: string;
  sexFilter: string;
  priceRange: [number, number];
  ageRange: [number, number];
  showUnsoldOnly: boolean;
};

export const useFilters = (horses: Horse[] = [], initialFilters?: Partial<FilterOptions>) => {
  const [filters, setFilters] = useState<FilterOptions>(() => ({
    searchQuery: initialFilters?.searchQuery || '',
    sexFilter: initialFilters?.sexFilter || 'all',
    priceRange: initialFilters?.priceRange || [0, 10000],
    ageRange: initialFilters?.ageRange || [0, 30],
    showUnsoldOnly: initialFilters?.showUnsoldOnly || false,
  }));

  // 入力がundefinedやnullの場合に空の配列を使用
  const safeHorses = Array.isArray(horses) ? horses : [];
  
  // フィルターを適用した馬のリストを返す
  const filteredHorses = safeHorses.filter(horse => {
    // 検索クエリによるフィルタリング
    const searchQuery = filters.searchQuery.toLowerCase();
    const matchesSearch = 
      horse.name?.toLowerCase().includes(searchQuery) ||
      horse.sire?.toLowerCase().includes(searchQuery) ||
      horse.dam?.toLowerCase().includes(searchQuery) ||
      horse.damsire?.toLowerCase().includes(searchQuery);

    // 性別によるフィルタリング
    const matchesSex = 
      filters.sexFilter === 'all' || 
      filters.sexFilter.split(',').includes(horse.sex);

    // 価格によるフィルタリング
    const horsePrice = horse.auction_histories?.[0]?.sold_price || 0;
    const numericHorsePrice = typeof horsePrice === 'string' ? parseFloat(horsePrice) || 0 : horsePrice;
    const matchesPrice = 
      numericHorsePrice >= filters.priceRange[0] && 
      (filters.priceRange[1] === 0 || 
       filters.priceRange[1] === 10000 || 
       numericHorsePrice <= filters.priceRange[1]);

    // 年齢によるフィルタリング
    const matchesAge = 
      horse.age !== undefined && 
      horse.age >= filters.ageRange[0] && 
      horse.age <= filters.ageRange[1];

    // 未落札のみ表示
    const matchesUnsold = 
      !filters.showUnsoldOnly || 
      (horse.auction_histories && horse.auction_histories.some((h: any) => isUnsoldHorse(h)));

    return (
      matchesSearch && 
      matchesSex && 
      matchesPrice && 
      matchesAge && 
      matchesUnsold
    );
  });

  // フィルターを更新する関数
  const updateFilters = useCallback((newFilters: Partial<FilterOptions>) => {
    setFilters(prev => ({
      ...prev,
      ...newFilters,
    }));
  }, []);

  // フィルターをリセットする関数
  const resetFilters = useCallback(() => {
    setFilters({
      searchQuery: '',
      sexFilter: 'all',
      priceRange: [0, 10000],
      ageRange: [0, 30],
      showUnsoldOnly: false,
    });
  }, []);

  // 常に同じ構造のオブジェクトを返す
  return {
    filteredHorses: filteredHorses || [],
    filters: filters || {
      searchQuery: '',
      sexFilter: 'all',
      priceRange: [0, 10000],
      ageRange: [0, 30],
      showUnsoldOnly: false,
    },
    updateFilters,
    resetFilters,
  };
};
