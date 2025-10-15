'use client';

import React from 'react';
import { Horse } from '../types/horse';
import SortableHeader from './common/SortableHeader';
import PriceDisplay from './common/PriceDisplay';
import WeightDisplay from './common/WeightDisplay';
import RoiBadge from './common/RoiBadge';
import HorseLink from './common/HorseLink';
import ExternalLink from './common/ExternalLink';
import DiseaseTags from './common/DiseaseTags';

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
            <SortableHeader label="馬名" columnKey={'name'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="性別" columnKey={'sex'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="年齢" columnKey={'age'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="父" columnKey={'sire'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="馬体重 (kg)" columnKey={'weight'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-right" />
            <SortableHeader label="落札価格" columnKey={'sold_price'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="落札時の賞金" columnKey={'total_prize_start'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="現在賞金" columnKey={'total_prize_latest'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <SortableHeader label="ROI" columnKey={'roi'} activeKey={sortKey} order={sortOrder} onSort={onSort} renderSortIcon={renderSortIcon} className="text-left" />
            <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">リンク</th>
            <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24">病歴</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {horses.map((horse, index) => (
            <tr key={`${horse.id || 'horse'}-${index}`} className="hover:bg-blue-50">
              <td className="px-3 py-2 font-medium text-gray-900">
                <HorseLink id={horse.id} name={horse.name} />
              </td>
              <td className="px-3 py-2">{horse.sex}</td>
              <td className="px-3 py-2">{displayAge(horse.age)}</td>
              <td className="px-3 py-2">{horse.sire}</td>
              <td className="px-3 py-2 text-right">
                <WeightDisplay value={horse.effectiveWeight} />
              </td>
              <td className="px-3 py-2">
                <PriceDisplay soldPrice={horse.sold_price} isUnsold={horse.is_unsold} unsold={horse.unsold} />
              </td>
              <td className="px-3 py-2">
                {horse.total_prize_start !== undefined && horse.total_prize_start !== null && horse.total_prize_start > 0
                  ? `${(Number(horse.total_prize_start) / 10000).toFixed(1)}万円` 
                  : '-'}
              </td>
              <td className="px-3 py-2">
                {horse.total_prize_latest !== undefined && horse.total_prize_latest !== null && horse.total_prize_latest > 0
                  ? `${(Number(horse.total_prize_latest) / 10000).toFixed(1)}万円`
                  : '-'}
              </td>
              <td className="px-3 py-2">
                <RoiBadge prizeMoney={horse.prize_money?.total_prize} soldPrice={horse.sold_price} />
              </td>
              <td className="px-3 py-2">
                <div className="flex flex-col gap-1 items-center">
                  <ExternalLink href={horse.jbis_url as string} label="JBIS" className="text-xs text-blue-600 hover:text-blue-800 underline whitespace-nowrap" title="JBISで詳細を確認" />
                  <ExternalLink href={horse.auction_url as string} label="サラオク" className="text-xs text-green-600 hover:text-green-800 underline whitespace-nowrap" title="オークションページで詳細を確認" />
                </div>
              </td>
              <td className="px-3 py-2 text-center">
                <DiseaseTags tags={horse.disease_tags} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
