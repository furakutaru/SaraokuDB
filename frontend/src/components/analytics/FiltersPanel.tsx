import React, { useMemo } from 'react';
import { Button } from '@/components/ui/button';

export type SexFilter = { male: boolean; female: boolean; gelding: boolean };

export type Filters = {
  sex: SexFilter;
  minAge: number;
  maxAge: number;
  sire: string;
  minROI: number;
  maxROI: number;
  minPrice: number;
  maxPrice: number;
  disease: 'any' | 'yes' | 'no';
  minWeight: number;
  maxWeight: number;
};

type Props = {
  filters: Filters;
  onChange: (next: Partial<Filters>) => void;
  onReset: () => void;
  sireSuggestions: string[];
  className?: string;
  onExportAll?: () => void;
  onExportFiltered?: () => void;
};

export const FiltersPanel: React.FC<Props> = ({ filters, onChange, onReset, sireSuggestions, className, onExportAll, onExportFiltered }) => {
  const dataListId = 'sire-suggestions';
  const dedupedSires = useMemo(() => Array.from(new Set(sireSuggestions)).slice(0, 1000), [sireSuggestions]);

  return (
    <div className={`bg-white rounded-md border p-3 ${className || ''}`}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">性別</span>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-1 text-xs"><input type="checkbox" className="h-3.5 w-3.5" checked={filters.sex.male} onChange={(e) => onChange({ sex: { ...filters.sex, male: e.target.checked } })} />牡</label>
            <label className="flex items-center gap-1 text-xs"><input type="checkbox" className="h-3.5 w-3.5" checked={filters.sex.female} onChange={(e) => onChange({ sex: { ...filters.sex, female: e.target.checked } })} />牝</label>
            <label className="flex items-center gap-1 text-xs"><input type="checkbox" className="h-3.5 w-3.5" checked={filters.sex.gelding} onChange={(e) => onChange({ sex: { ...filters.sex, gelding: e.target.checked } })} />セ</label>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">年齢</span>
          <div className="flex items-center gap-1.5">
            <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minAge} min={0} max={filters.maxAge} onChange={(e) => onChange({ minAge: parseInt(e.target.value || '0', 10) })} />
            <span>〜</span>
            <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxAge} min={filters.minAge} max={30} onChange={(e) => onChange({ maxAge: parseInt(e.target.value || '0', 10) })} />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">父</span>
          <input list={dataListId} className="w-full border rounded px-2 py-1 h-7 text-xs" placeholder="例: アグネスタキオン" value={filters.sire} onChange={(e) => onChange({ sire: e.target.value })} />
          <datalist id={dataListId}>
            {dedupedSires.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">ROI</span>
          <div className="flex items-center gap-1.5">
            <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minROI} min={0} onChange={(e) => onChange({ minROI: parseFloat(e.target.value || '0') })} />
            <span>〜</span>
            <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxROI} min={filters.minROI} onChange={(e) => onChange({ maxROI: parseFloat(e.target.value || '0') })} />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">落札価格</span>
          <div className="flex items-center gap-1.5">
            <input type="number" className="w-24 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minPrice} min={0} onChange={(e) => onChange({ minPrice: parseInt(e.target.value || '0', 10) })} />
            <span>〜</span>
            <input type="number" className="w-24 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxPrice} min={filters.minPrice} onChange={(e) => onChange({ maxPrice: parseInt(e.target.value || '0', 10) })} />
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">病歴</span>
          <select className="w-full border rounded px-2 py-1 h-7 text-xs" value={filters.disease} onChange={(e) => onChange({ disease: e.target.value as Filters['disease'] })}>
            <option value="any">指定なし</option>
            <option value="yes">病歴あり</option>
            <option value="no">病歴なし</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-700 whitespace-nowrap">馬体重</span>
          <div className="flex items-center gap-1.5">
            <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minWeight} min={0} onChange={(e) => onChange({ minWeight: parseInt(e.target.value || '0', 10) })} />
            <span>〜</span>
            <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxWeight} min={filters.minWeight} onChange={(e) => onChange({ maxWeight: parseInt(e.target.value || '0', 10) })} />
          </div>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-between">
        <div className="flex gap-2">
          <Button variant="outline" className="h-8 px-2 py-1 text-xs" onClick={onExportAll}>
            全体CSV
          </Button>
          <Button variant="outline" className="h-8 px-2 py-1 text-xs" onClick={onExportFiltered}>
            絞り込みCSV
          </Button>
        </div>
        <Button variant="outline" className="h-8 px-2 py-1 text-xs" onClick={onReset}>フィルターをリセット</Button>
      </div>
    </div>
  );
};
