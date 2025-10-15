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
  if (price !== null && price > 0) {
    return <>{formatPrice(price)}</>;
  }
  if (isUnsold === true || unsold === true) {
    return <>主取り</>;
  }
  return <>-</>;
}
