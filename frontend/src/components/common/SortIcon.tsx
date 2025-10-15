'use client';

import React from 'react';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { Horse } from '../../types/horse';

interface SortIconProps {
  columnKey: keyof Horse;
  activeKey: keyof Horse;
  order: 'asc' | 'desc';
}

export default function SortIcon({ columnKey, activeKey, order }: SortIconProps) {
  if (activeKey !== columnKey) return <FaSort className="ml-1 opacity-30" />;
  return order === 'asc' ? <FaSortUp className="ml-1" /> : <FaSortDown className="ml-1" />;
}
