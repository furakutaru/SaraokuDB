'use client';

import React from 'react';

interface DiseaseTagsProps {
  tags: any;
}

const isNoDisease = (tags: any) => {
  if (tags === undefined || tags === null || tags === '') return true;
  if (Array.isArray(tags)) {
    if (tags.length === 0) return true;
    return tags.every((tag) => {
      const strTag = String(tag).trim();
      return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
    });
  }
  const strTag = String(tags).trim();
  return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
};

export default function DiseaseTags({ tags }: DiseaseTagsProps) {
  return isNoDisease(tags) ? (
    <span className="text-xs font-medium bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">なし</span>
  ) : (
    <span className="text-xs font-medium bg-pink-100 text-pink-800 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">あり</span>
  );
}
