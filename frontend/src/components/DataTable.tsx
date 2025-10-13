'use client';

import React from 'react';
import Link from 'next/link';
import { Button } from './ui/button';
import { Horse } from '../types/horse';
import { formatPrice, calcROI } from '../utils/formatters';

export type DisplayHorse = Horse & { [key: string]: any };

interface DataTableProps {
  horses: DisplayHorse[];
  sortKey: keyof Horse;
  sortOrder: 'asc' | 'desc';
  onSort: (key: keyof Horse) => void;
  renderSortIcon: (key: keyof Horse, currentKey: keyof Horse, currentOrder: 'asc' | 'desc') => JSX.Element;
}

const displayAge = (age: string | number | null | undefined): string => {
  if (age === null || age === undefined || age === '') return '-';
  return `${age}歳`;
};

export default function DataTable({ horses, sortKey, sortOrder, onSort, renderSortIcon }: DataTableProps) {
  return (
    <div className="overflow-x-auto bg-white rounded-lg shadow">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-100">
          <tr>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('name')}>馬名{renderSortIcon('name', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('sex')}>性別{renderSortIcon('sex', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('age')}>年齢{renderSortIcon('age', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('sire')}>父{renderSortIcon('sire', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('weight')}>馬体重 (kg){renderSortIcon('weight', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('sold_price')}>落札価格{renderSortIcon('sold_price', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('total_prize_start')}>オークション時賞金{renderSortIcon('total_prize_start', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('total_prize_latest')}>現在賞金{renderSortIcon('total_prize_latest', sortKey, sortOrder)}</th>
            <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => onSort('roi')}>ROI{renderSortIcon('roi', sortKey, sortOrder)}</th>
            <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">リンク</th>
            <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24">病歴</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {horses.map((horse, index) => (
            <tr key={`${horse.id || 'horse'}-${index}`} className="hover:bg-blue-50">
              <td className="px-3 py-2 font-medium text-gray-900">
                {horse.id ? (
                  <Link href={`/horses/${horse.id}`} className="hover:underline text-blue-700">
                    {horse.name}
                  </Link>
                ) : (
                  <span>{horse.name}</span>
                )}
              </td>
              <td className="px-3 py-2">{horse.sex}</td>
              <td className="px-3 py-2">{displayAge(horse.age)}</td>
              <td className="px-3 py-2">{horse.sire}</td>
              <td className="px-3 py-2 text-right">
                {horse.effectiveWeight !== undefined ? `${horse.effectiveWeight}kg` : '-'}
              </td>
              <td className="px-3 py-2">
                {horse.sold_price && horse.sold_price > 0
                  ? formatPrice(horse.sold_price)
                  : (horse.is_unsold || horse.unsold) ? '主取り' : '-'}
              </td>
              <td className="px-3 py-2">-</td>
              <td className="px-3 py-2">
                {horse.prize_money?.total_prize !== undefined ? `${horse.prize_money.total_prize}万円` : '-'}
              </td>
              <td className="px-3 py-2">
                {horse.prize_money?.total_prize !== undefined
                  ? calcROI(horse.prize_money.total_prize, horse.sold_price ?? undefined)
                  : calcROI(undefined, horse.sold_price ?? undefined)}
              </td>
              <td className="px-3 py-2">
                <div className="flex flex-col gap-1 items-center">
                  {horse.jbis_url && (
                    <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:text-blue-800 underline whitespace-nowrap" title="JBISで詳細を確認">JBIS</a>
                  )}
                  {horse.auction_url && (
                    <a href={horse.auction_url} target="_blank" rel="noopener noreferrer" className="text-xs text-green-600 hover:text-green-800 underline whitespace-nowrap" title="オークションページで詳細を確認">サラオク</a>
                  )}
                </div>
              </td>
              <td className="px-3 py-2 text-center">
                {(() => {
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
                  return isNoDisease(horse.disease_tags) ? (
                    <span className="text-xs font-medium bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">なし</span>
                  ) : (
                    <span className="text-xs font-medium bg-pink-100 text-pink-800 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">あり</span>
                  );
                })()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
