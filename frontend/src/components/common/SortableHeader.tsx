'use client';

import React from 'react';
import { Horse } from '../../types/horse';

// Horse 型を拡張して weight プロパティを含める
type HorseWithWeight = Horse & {
  weight?: number | null;
};

interface SortableHeaderProps {
  label: string;
  columnKey: keyof HorseWithWeight;
  activeKey: keyof HorseWithWeight;
  order: 'asc' | 'desc';
  onSort: (key: keyof HorseWithWeight) => void;
  renderSortIcon: (key: keyof HorseWithWeight, currentKey: keyof HorseWithWeight, currentOrder: 'asc' | 'desc') => JSX.Element;
  className?: string;
}

export default function SortableHeader({ label, columnKey, activeKey, order, onSort, renderSortIcon, className }: SortableHeaderProps) {
  const base = 'px-3 py-2 text-xs font-medium text-gray-500 uppercase cursor-pointer';
  const align = className?.includes('text-right') ? 'text-right' : 'text-left';
  return (
    <th className={`${base} ${align}`} onClick={() => onSort(columnKey)}>
      {label}
      {renderSortIcon(columnKey, activeKey, order)}
    </th>
  );
}
