'use client';

import React from 'react';
import { calcROI } from '../../utils/formatters';

interface RoiBadgeProps {
  prizeMoney: number | string | undefined;
  soldPrice: number | string | null | undefined;
}

export default function RoiBadge({ prizeMoney, soldPrice }: RoiBadgeProps) {
  const prize = typeof prizeMoney === 'string' ? Number(prizeMoney) : prizeMoney;
  const sold = typeof soldPrice === 'string' ? Number(soldPrice) : soldPrice ?? undefined;
  // 既存の表示と完全一致させるため、calcROI の出力をそのまま返す
  return <>{calcROI(prize, sold)}</>;
}
