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
  sortKey?: string;
  sortOrder?: SortOrder;
  onSort?: (key: string) => void;
};

export const HorseTable = ({ horses, onRowClick, sortKey, sortOrder, onSort }: HorseTableProps) => {
  // ソートアイコン
  const renderSortIcon = (key: string) => {
    if (sortKey !== key) return <FaSort className="inline ml-1 text-gray-400" />;
    return sortOrder === 'asc' ?
      <FaSortUp className="inline ml-1 text-blue-600" /> :
      <FaSortDown className="inline ml-1 text-blue-600" />;
  };

  const handleSortClick = (key: string) => {
    if (onSort) {
      onSort(key);
    }
  };

  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow w-full">
      <table className="min-w-full divide-y divide-gray-200 w-full">
        <thead className="bg-gray-100">
          <tr>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('name')}
            >
              馬名{renderSortIcon('name')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('sex')}
            >
              性別{renderSortIcon('sex')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('age')}
            >
              年齢{renderSortIcon('age')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('sire')}
            >
              父{renderSortIcon('sire')}
            </th>
            <th
              className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('weight')}
            >
              馬体重 (kg){renderSortIcon('weight')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('sold_price')}
            >
              落札価格{renderSortIcon('sold_price')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('total_prize_start')}
            >
              落札時賞金{renderSortIcon('total_prize_start')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('total_prize_latest')}
            >
              現在賞金{renderSortIcon('total_prize_latest')}
            </th>
            <th
              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer"
              onClick={() => handleSortClick('roi')}
            >
              ROI{renderSortIcon('roi')}
            </th>
            <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">
              リンク
            </th>
            <th
              className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24 cursor-pointer hover:bg-gray-100"
              onClick={() => handleSortClick('disease_tags')}
            >
              病歴
              {renderSortIcon('disease_tags')}
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {horses.map((horse) => {
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
