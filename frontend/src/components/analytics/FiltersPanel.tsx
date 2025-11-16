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
};

export const FiltersPanel: React.FC<Props> = ({ filters, onChange, onReset, sireSuggestions, className }) => {
  const dataListId = 'sire-suggestions';
  const dedupedSires = useMemo(() => Array.from(new Set(sireSuggestions)).slice(0, 1000), [sireSuggestions]);

  return (
    <div className={`bg-white rounded-md border p-4 ${className || ''}`}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div>
          <div className="text-sm text-gray-700 mb-2">性別</div>
          <div className="flex items-center gap-4">
            <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={filters.sex.male} onChange={(e) => onChange({ sex: { ...filters.sex, male: e.target.checked } })} />牡</label>
            <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={filters.sex.female} onChange={(e) => onChange({ sex: { ...filters.sex, female: e.target.checked } })} />牝</label>
            <label className="flex items-center gap-1 text-sm"><input type="checkbox" checked={filters.sex.gelding} onChange={(e) => onChange({ sex: { ...filters.sex, gelding: e.target.checked } })} />セ</label>
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-700 mb-2">年齢</div>
          <div className="flex items-center gap-2">
            <input type="number" className="w-24 border rounded px-2 py-1" value={filters.minAge} min={0} max={filters.maxAge} onChange={(e) => onChange({ minAge: parseInt(e.target.value || '0', 10) })} />
            <span>〜</span>
            <input type="number" className="w-24 border rounded px-2 py-1" value={filters.maxAge} min={filters.minAge} max={30} onChange={(e) => onChange({ maxAge: parseInt(e.target.value || '0', 10) })} />
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-700 mb-2">父（種牡馬）</div>
          <input list={dataListId} className="w-full border rounded px-2 py-1" placeholder="例: アグネスタキオン" value={filters.sire} onChange={(e) => onChange({ sire: e.target.value })} />
          <datalist id={dataListId}>
            {dedupedSires.map((s) => (
              <option key={s} value={s} />
            ))}
          </datalist>
        </div>

        <div>
          <div className="text-sm text-gray-700 mb-2">ROI</div>
          <div className="flex items-center gap-2">
            <input type="number" className="w-24 border rounded px-2 py-1" value={filters.minROI} min={0} onChange={(e) => onChange({ minROI: parseFloat(e.target.value || '0') })} />
            <span>〜</span>
            <input type="number" className="w-24 border rounded px-2 py-1" value={filters.maxROI} min={filters.minROI} onChange={(e) => onChange({ maxROI: parseFloat(e.target.value || '0') })} />
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-700 mb-2">落札価格</div>
          <div className="flex items-center gap-2">
            <input type="number" className="w-28 border rounded px-2 py-1" value={filters.minPrice} min={0} onChange={(e) => onChange({ minPrice: parseInt(e.target.value || '0', 10) })} />
            <span>〜</span>
            <input type="number" className="w-28 border rounded px-2 py-1" value={filters.maxPrice} min={filters.minPrice} onChange={(e) => onChange({ maxPrice: parseInt(e.target.value || '0', 10) })} />
          </div>
        </div>

        <div>
          <div className="text-sm text-gray-700 mb-2">病歴</div>
          <select className="w-full border rounded px-2 py-1" value={filters.disease} onChange={(e) => onChange({ disease: e.target.value as Filters['disease'] })}>
            <option value="any">指定なし</option>
            <option value="yes">病歴あり</option>
            <option value="no">病歴なし</option>
          </select>
        </div>

        <div>
          <div className="text-sm text-gray-700 mb-2">馬体重(kg)</div>
          <div className="flex items-center gap-2">
            <input type="number" className="w-24 border rounded px-2 py-1" value={filters.minWeight} min={0} onChange={(e) => onChange({ minWeight: parseInt(e.target.value || '0', 10) })} />
            <span>〜</span>
            <input type="number" className="w-24 border rounded px-2 py-1" value={filters.maxWeight} min={filters.minWeight} onChange={(e) => onChange({ maxWeight: parseInt(e.target.value || '0', 10) })} />
          </div>
        </div>
      </div>

      <div className="mt-4 flex justify-end">
        <Button variant="outline" onClick={onReset}>フィルターをリセット</Button>
      </div>
    </div>
  );
};
