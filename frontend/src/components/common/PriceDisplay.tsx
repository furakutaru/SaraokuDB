'use client';

import React from 'react';
import { formatPrice } from '../../utils/formatters';

interface PriceDisplayProps {
  soldPrice: number | null | undefined;
  isUnsold?: boolean;
  unsold?: boolean;
}

export default function PriceDisplay({ soldPrice, isUnsold, unsold }: PriceDisplayProps) {
  const price = typeof soldPrice === 'number' ? soldPrice : null;
  
  // 主取りの判定
  const isActuallyUnsold = isUnsold || unsold || (price !== null && price <= 0);
  
  if (price !== null && price > 0 && !isActuallyUnsold) {
    return <>{formatPrice(price)}</>;
  }
  
  // 主取りの場合の表示
  return <span className="text-red-600 font-semibold">主取り</span>;
}
