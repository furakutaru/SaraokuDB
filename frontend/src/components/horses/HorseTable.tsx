import { useState } from 'react';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { HorseTableRow } from './HorseTableRow';
import type { HorseWithCalculations } from '../../types/horse';
import { formatPrice } from '../../utils/format';

type SortKey = 'name' | 'sex' | 'age' | 'sire' | 'weight' | 'sold_price' | 
  'total_prize_start' | 'total_prize_latest' | 'roi' | 'disease_tags';
type SortOrder = 'asc' | 'desc';

type HorseTableProps = {
  horses: HorseWithCalculations[];
  onRowClick: (id: string | number) => void;
};

export const HorseTable = ({ horses, onRowClick }: HorseTableProps) => {
  const [sortKey, setSortKey] = useState<SortKey>('name');
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc');

  // ソート関数の型定義
  type SortFunction = (a: HorseWithCalculations, b: HorseWithCalculations) => number;
  
  // ソート関数のマップ
  const sortFunctions: Record<SortKey, SortFunction> = {
    name: (a, b) => (a?.name ?? '').localeCompare(b?.name ?? '', 'ja'),
    sex: (a, b) => (a?.sex ?? '').localeCompare(b?.sex ?? '', 'ja'),
    weight: (a, b) => (a?.weight ?? 0) - (b?.weight ?? 0),
    age: (a, b) => {
      const ageA = typeof a?.age === 'number' ? a.age : (a?.age ? parseFloat(String(a.age)) : 0);
      const ageB = typeof b?.age === 'number' ? b.age : (b?.age ? parseFloat(String(b.age)) : 0);
      return ageA - ageB;
    },
    sire: (a, b) => (a?.sire ?? '').localeCompare(b?.sire ?? '', 'ja'),
    sold_price: (a, b) => {
      const aPrice = a?.sold_price !== null && a?.sold_price !== undefined ? 
        (typeof a.sold_price === 'number' ? a.sold_price : 0) : 0;
      const bPrice = b.sold_price !== null && b.sold_price !== undefined ? 
        (typeof b.sold_price === 'number' ? b.sold_price : 0) : 0;
      return aPrice - bPrice;
    },
    total_prize_start: (a, b) => (a.total_prize_start || 0) - (b.total_prize_start || 0),
    total_prize_latest: (a, b) => (a.total_prize_latest || 0) - (b.total_prize_latest || 0),
    roi: (a, b) => {
      const aSoldPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bSoldPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;
      
      const aEarnedPrize = (a.total_prize_latest || 0) - (a.total_prize_start || 0);
      const bEarnedPrize = (b.total_prize_latest || 0) - (b.total_prize_start || 0);
      
      const aROI = aSoldPrice > 0 ? aEarnedPrize / aSoldPrice : 0;
      const bROI = bSoldPrice > 0 ? bEarnedPrize / bSoldPrice : 0;
      
      return aROI - bROI;
    },
    disease_tags: (a, b) => {
      const hasDisease = (horse: HorseWithCalculations) => {
        const tags = (horse as any).disease_tags;
        if (!tags || tags.length === 0) return false;
        return !tags.every((tag: any) => {
          const strTag = String(tag).trim();
          return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
        });
      };
      
      const aHasDisease = hasDisease(a) ? 1 : 0;
      const bHasDisease = hasDisease(b) ? 1 : 0;
      
      return aHasDisease - bHasDisease;
    },
  };

  // ソートハンドラー
  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  // ソートアイコン
  const renderSortIcon = (key: SortKey) => {
    if (sortKey !== key) return <FaSort className="inline ml-1 text-gray-400" />;
    return sortOrder === 'asc' ? 
      <FaSortUp className="inline ml-1 text-blue-600" /> : 
      <FaSortDown className="inline ml-1 text-blue-600" />;
  };

  // ソートを適用した馬のリスト
  const sortedHorses = [...horses].sort((a, b) => {
    try {
      const res = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? res : -res;
    } catch (error) {
      console.error('ソート中にエラーが発生しました:', error);
      return 0;
    }
  });

  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow w-full">
      <table className="min-w-full divide-y divide-gray-200 w-full">
        <thead className="bg-gray-100">
          <tr>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('name')}
            >
              馬名{renderSortIcon('name')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('sex')}
            >
              性別{renderSortIcon('sex')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('age')}
            >
              年齢{renderSortIcon('age')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('sire')}
            >
              父{renderSortIcon('sire')}
            </th>
            <th 
              className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('weight')}
            >
              馬体重 (kg){renderSortIcon('weight')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('sold_price')}
            >
              落札価格{renderSortIcon('sold_price')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('total_prize_start')}
            >
              落札時賞金{renderSortIcon('total_prize_start')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('total_prize_latest')}
            >
              現在賞金{renderSortIcon('total_prize_latest')}
            </th>
            <th 
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" 
              onClick={() => handleSort('roi')}
            >
              ROI{renderSortIcon('roi')}
            </th>
            <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">
              リンク
            </th>
            <th 
              className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSort('disease_tags')}
            >
              病歴
              {sortKey === 'disease_tags' ? (
                sortOrder === 'asc' ? 
                  <FaSortUp className="inline ml-1 text-blue-600" /> : 
                  <FaSortDown className="inline ml-1 text-blue-600" />
              ) : (
                <FaSort className="inline ml-1 text-gray-400" />
              )}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {sortedHorses.map((horse) => {
            return (
              <HorseTableRow 
                key={horse.id} 
                horse={horse} 
                onRowClick={onRowClick} 
              />
            );
          })}
        </tbody>
      </table>
    </div>
  );
};
