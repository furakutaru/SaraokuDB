import React from 'react';
import { SortableField } from '../../types';

interface SortControlsProps {
  sortField: SortableField;
  sortOrder: 'asc' | 'desc';
  onSortFieldChange: (field: SortableField) => void;
  onSortOrderChange: (order: 'asc' | 'desc') => void;
  className?: string;
}

/**
 * ソートコントロールコンポーネント
 * ソートフィールドの選択と昇順/降順の切り替えを提供
 */
const SortControls: React.FC<SortControlsProps> = ({
  sortField,
  sortOrder,
  onSortFieldChange,
  onSortOrderChange,
  className = '',
}) => {
  const sortOptions = [
    { value: 'name', label: '馬名' },
    { value: 'sold_price', label: '落札価格' },
    { value: 'auction_date', label: 'オークション日' },
    { value: 'total_prize_latest', label: '総賞金' },
    { value: 'age', label: '年齢' },
  ] as const;

  return (
    <div className={`flex items-center space-x-4 ${className}`}>
      <div>
        <label htmlFor="sort-field" className="block text-sm font-medium text-gray-700 mb-1">
          並べ替え
        </label>
        <select
          id="sort-field"
          className="block w-full pl-3 pr-10 py-2 text-base border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
          value={sortField}
          onChange={(e) => onSortFieldChange(e.target.value as SortableField)}
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
      <div className="mt-6">
        <button
          type="button"
          className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          onClick={() => onSortOrderChange(sortOrder === 'asc' ? 'desc' : 'asc')}
          aria-label={sortOrder === 'asc' ? '昇順' : '降順'}
        >
          {sortOrder === 'asc' ? '昇順' : '降順'}
          {sortOrder === 'asc' ? (
            <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.293 9.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 7.414V15a1 1 0 11-2 0V7.414L6.707 9.707a1 1 0 01-1.414 0z" clipRule="evenodd" />
            </svg>
          ) : (
            <svg className="ml-2 -mr-1 h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M14.707 10.293a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 111.414-1.414L9 12.586V5a1 1 0 012 0v7.586l2.293-2.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          )}
        </button>
      </div>
    </div>
  );
};

export default SortControls;
