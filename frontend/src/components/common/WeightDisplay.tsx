'use client';

import React from 'react';

interface WeightDisplayProps {
  value: number | undefined | null;
}

export default function WeightDisplay({ value }: WeightDisplayProps) {
  if (value === undefined || value === null) return <>-</>;
  return <>{`${value}kg`}</>;
}
