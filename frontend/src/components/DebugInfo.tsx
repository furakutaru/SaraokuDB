'use client';

import React from 'react';

interface DebugInfoProps {
  count: number;
  showType: string;
  filterBySex: string;
  filterByAge: string;
  filterBySire: string;
  filterByDam: string;
}

export default function DebugInfo({ count, showType, filterBySex, filterByAge, filterBySire, filterByDam }: DebugInfoProps) {
  return (
    <div className="mb-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
      <p>デバッグ情報: 表示中の馬の数: {count}</p>
      <p>表示タイプ: {showType}</p>
      <p>フィルター: 性別={filterBySex}, 年齢={filterByAge}, 父馬={filterBySire}, 母馬={filterByDam}</p>
    </div>
  );
}
