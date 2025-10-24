import { useState, useCallback } from 'react';
import { Horse, SortOrder, SortableField } from '../types';

type UseSortingReturn = {
  sortField: SortableField;
  sortOrder: SortOrder;
  sortedHorses: Horse[];
  handleSort: (field: SortableField) => void;
};

export const useSorting = (horses: Horse[] = []): UseSortingReturn => {
  const [sortState, setSortState] = useState<{
    field: SortableField;
    order: SortOrder;
  }>({ field: 'name', order: 'asc' });
  
  const { field: sortField, order: sortOrder } = sortState;

  // 入力がundefinedやnullの場合に空の配列を使用
  const safeHorses = Array.isArray(horses) ? horses : [];
  
  const sortedHorses = [...safeHorses].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    // ソート対象の値を取得
    if (sortField === 'sold_price') {
      // デバッグ用: ソート前の値をログに出力
      console.log('Before sorting - a:', {
        raw: a.auction_histories?.[0]?.sold_price,
        type: typeof a.auction_histories?.[0]?.sold_price
      });
      console.log('Before sorting - b:', {
        raw: b.auction_histories?.[0]?.sold_price,
        type: typeof b.auction_histories?.[0]?.sold_price
      });

      // 文字列から数値に変換（カンマや「万円」を除去）
      const parsePrice = (price: any): number => {
        console.log('Parsing price:', { price, type: typeof price });
        
        if (price === null || price === undefined) return 0;
        if (typeof price === 'number') return price;
        if (typeof price !== 'string') return 0;
        
        // 金額から数字以外と「万」を除去
        const numStr = price.replace(/[^0-9.]/g, '');
        const result = parseFloat(numStr) || 0;
        console.log('Parsed result:', { price, numStr, result });
        return result;
      };

      aValue = parsePrice(a.auction_histories?.[0]?.sold_price);
      bValue = parsePrice(b.auction_histories?.[0]?.sold_price);
      
      // デバッグ用: ソートに使用する値をログに出力
      console.log('Sorting values:', { aValue, bValue, sortOrder });
    } else if (sortField === 'age') {
      aValue = a.age || 0;
      bValue = b.age || 0;
    } else if (sortField === 'total_prize_latest' || sortField === 'total_prize_start') {
      // total_prize_latest の代わりに total_prize_start を使用
      const aPrize = a.total_prize_start || 0;
      const bPrize = b.total_prize_start || 0;
      
      // トップページと同様のロジックでソート
      aValue = typeof aPrize === 'number' ? aPrize : 0;
      bValue = typeof bPrize === 'number' ? bPrize : 0;
    } else {
      // デフォルトは名前でソート
      // auction_date の場合は配列の最初の要素を使用
      if (sortField === 'auction_date') {
        const getDateValue = (date: any): string => {
          if (!date) return '';
          return Array.isArray(date) ? date[0] || '' : date;
        };
        
        aValue = getDateValue(a[sortField as keyof Horse]);
        bValue = getDateValue(b[sortField as keyof Horse]);
      } else {
        aValue = a[sortField as keyof Horse] || '';
        bValue = b[sortField as keyof Horse] || '';
      }
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
    setSortState(prev => ({
      field,
      order: prev.field === field && prev.order === 'asc' ? 'desc' : 'asc'
    }));
  }, []);

  // 常に同じ構造のオブジェクトを返す
  return {
    sortedHorses: sortedHorses || [],
    sortField: sortField || 'name',
    sortOrder: sortOrder || 'asc',
    handleSort,
  };
};
