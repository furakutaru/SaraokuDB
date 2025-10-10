import { useState, useCallback } from 'react';
import { Horse, SortOrder, SortableField } from '../types';

type UseSortingReturn = {
  sortField: SortableField;
  sortOrder: SortOrder;
  sortedHorses: Horse[];
  handleSort: (field: SortableField) => void;
};

export const useSorting = (horses: Horse[]): UseSortingReturn => {
  const [sortField, setSortField] = useState<SortableField>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  const sortedHorses = [...horses].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    // ソート対象の値を取得
    if (sortField === 'sold_price') {
      aValue = a.auction_histories?.[0]?.sold_price || 0;
      bValue = b.auction_histories?.[0]?.sold_price || 0;
    } else if (sortField === 'age') {
      aValue = a.age || 0;
      bValue = b.age || 0;
    } else if (sortField === 'total_prize_latest') {
      aValue = a.total_prize_latest || 0;
      bValue = b.total_prize_latest || 0;
    } else {
      // デフォルトは名前でソート
      aValue = a[sortField as keyof Horse] || '';
      bValue = b[sortField as keyof Horse] || '';
    }

    // 数値の比較
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    }
    // 文字列の比較
    return sortOrder === 'asc'
      ? String(aValue).localeCompare(String(bValue))
      : String(bValue).localeCompare(String(aValue));
  });

  const handleSort = useCallback((field: SortableField) => {
    setSortField(field);
    setSortOrder(prevOrder => 
      prevOrder === 'asc' && sortField === field ? 'desc' : 'asc'
    );
  }, [sortField]);

  return {
    sortField,
    sortOrder,
    sortedHorses,
    handleSort,
  };
};
