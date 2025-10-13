'use client';

import React from 'react';
import { formatPrice } from '../utils/formatters';

interface SummaryBarProps {
  count: number;
  averagePrice?: number | null;
  avgROI: number;
}

export default function SummaryBar({ count, averagePrice, avgROI }: SummaryBarProps) {
  return (
    <div className="mb-6 text-lg font-semibold text-gray-700 flex flex-wrap gap-8">
      <span>総馬数: {count}</span>
      <span>平均落札価格: {averagePrice ? formatPrice(averagePrice) : 'N/A'}</span>
      <span>平均ROI: {avgROI.toFixed(2)}</span>
    </div>
  );
}
