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

export const useFilters = (horses: Horse[], initialFilters?: Partial<FilterOptions>) => {
  const [filters, setFilters] = useState<FilterOptions>({
    searchQuery: '',
    sexFilter: 'all',
    priceRange: [0, 0],
    ageRange: [0, 30],
    showUnsoldOnly: false,
    ...initialFilters,
  });

  // フィルターを適用した馬のリストを返す
  const filteredHorses = horses.filter(horse => {
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
      horse.sex === filters.sexFilter;

    // 価格によるフィルタリング
    const horsePrice = horse.auction_histories?.[0]?.sold_price || 0;
    const numericHorsePrice = typeof horsePrice === 'string' ? parseFloat(horsePrice) || 0 : horsePrice;
    const matchesPrice = 
      numericHorsePrice >= filters.priceRange[0] && 
      (filters.priceRange[1] === 0 || numericHorsePrice <= filters.priceRange[1]);

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
      priceRange: [0, 0],
      ageRange: [0, 30],
      showUnsoldOnly: false,
    });
  }, []);

  return {
    filteredHorses,
    filters,
    updateFilters,
    resetFilters,
  };
};
