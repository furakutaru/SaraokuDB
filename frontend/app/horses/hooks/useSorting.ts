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
  
  console.log('=== useSorting ソート開始 ===');
  console.log('ソートフィールド:', sortField, 'ソート順:', sortOrder);
  console.log('ソート前の馬の数:', safeHorses.length);
  
  const sortedHorses = [...safeHorses].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    // ソート対象の値を取得
    if (sortField === 'sold_price') {
      // デバッグ用: ソート前の値をログに出力
      console.log('Before sorting - a:', {
        raw: a.sold_price,
        type: typeof a.sold_price,
        auction_histories: a.auction_histories?.[0]?.sold_price
      });
      console.log('Before sorting - b:', {
        raw: b.sold_price,
        type: typeof b.sold_price,
        auction_histories: b.auction_histories?.[0]?.sold_price
      });

      // 数値に変換
      aValue = a.sold_price !== null && a.sold_price !== undefined ? a.sold_price : 0;
      bValue = b.sold_price !== null && b.sold_price !== undefined ? b.sold_price : 0;
      
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

    // キャンセル（主取り）の処理
    const isACanceled = a.auction_histories?.[0]?.canceled || false;
    const isBCanceled = b.auction_histories?.[0]?.canceled || false;

    // キャンセル状態が異なる場合、キャンセルを先頭に
    if (isACanceled !== isBCanceled) {
      return isACanceled ? -1 : 1;
    }
    
    // 両方キャンセルの場合はIDでソート
    if (isACanceled && isBCanceled) {
      const aId = Number(a.id) || 0;
      const bId = Number(b.id) || 0;
      return aId - bId; // キャンセル同士はID順
    }
    
    // 数値の比較（両方キャンセルでない場合）
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      // 主取り（キャンセル）の場合は0円相当として扱う
      const aPrice = isACanceled ? 0 : aValue;
      const bPrice = isBCanceled ? 0 : bValue;
      
      // 価格で比較（昇順）
      if (sortOrder === 'asc') {
        return aPrice - bPrice;
      }
      
      // 両方0の場合はIDでソート
      if (aValue === 0 && bValue === 0) {
        const aId = Number(a.id) || 0;
        const bId = Number(b.id) || 0;
        return sortOrder === 'asc' ? aId - bId : bId - aId;
      }
      // 片方が0の場合は0を後ろに
      if (aValue === 0) return 1;
      if (bValue === 0) return -1;
      
      // 通常の数値比較
      const result = sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
      console.log('数値比較:', { aValue, bValue, sortOrder, result });
      return result;
    }
    // 文字列の比較
    return sortOrder === 'asc'
      ? String(aValue).localeCompare(String(bValue))
      : String(bValue).localeCompare(String(aValue));
  });

  const handleSort = useCallback((field: SortableField) => {
    console.log('=== useSorting handleSort 呼び出し ===');
    console.log('クリックされたフィールド:', field);
    setSortState(prev => {
      const newOrder = prev.field === field && prev.order === 'asc' ? 'desc' : 'asc';
      console.log('新しいソート状態:', { field, order: newOrder });
      return {
        field,
        order: newOrder
      };
    });
  }, []);

  // 常に同じ構造のオブジェクトを返す
  return {
    sortedHorses: sortedHorses || [],
    sortField: sortField || 'name',
    sortOrder: sortOrder || 'asc',
    handleSort,
  };
};
