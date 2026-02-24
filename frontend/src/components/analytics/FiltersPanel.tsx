import React, { useMemo } from 'react';
import { Button } from '@/components/ui/button';

export type SexFilter = { male: boolean; female: boolean; gelding: boolean };

export type Filters = {
    sex: SexFilter;
    minAge: number | null;
    maxAge: number | null;
    sire: string;
    minROI: number | null;
    maxROI: number | null;
    minPrice: number | null;
    maxPrice: number | null;
    disease: 'any' | 'yes' | 'no';
    minWeight: number | null;
    maxWeight: number | null;
    isBroodmare: 'any' | 'yes' | 'no';
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">性別</span>
                    <div className="flex items-center gap-3">
                        <label className="flex items-center gap-1 text-xs cursor-pointer">
                            <input type="checkbox" className="h-3.5 w-3.5" checked={filters.sex.male} onChange={(e) => onChange({ sex: { ...filters.sex, male: e.target.checked } })} />
                            牡
                        </label>
                        <label className="flex items-center gap-1 text-xs cursor-pointer">
                            <input type="checkbox" className="h-3.5 w-3.5" checked={filters.sex.female} onChange={(e) => onChange({ sex: { ...filters.sex, female: e.target.checked } })} />
                            牝
                        </label>
                        <label className="flex items-center gap-1 text-xs cursor-pointer">
                            <input type="checkbox" className="h-3.5 w-3.5" checked={filters.sex.gelding} onChange={(e) => onChange({ sex: { ...filters.sex, gelding: e.target.checked } })} />
                            セ
                        </label>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">年齢</span>
                    <div className="flex items-center gap-1.5">
                        <input type="number" className="w-16 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minAge ?? ''} onChange={(e) => onChange({ minAge: e.target.value === '' ? null : parseInt(e.target.value, 10) })} />
                        <span>〜</span>
                        <input type="number" className="w-16 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxAge ?? ''} onChange={(e) => onChange({ maxAge: e.target.value === '' ? null : parseInt(e.target.value, 10) })} />
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">父</span>
                    <input list={dataListId} className="w-full border rounded px-2 py-1 h-7 text-xs" placeholder="アグネスタキオン" value={filters.sire} onChange={(e) => onChange({ sire: e.target.value })} />
                    <datalist id={dataListId}>
                        {dedupedSires.map((s) => (
                            <option key={s} value={s} />
                        ))}
                    </datalist>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">ROI</span>
                    <div className="flex items-center gap-1.5">
                        <input type="number" className="w-16 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minROI ?? ''} onChange={(e) => onChange({ minROI: e.target.value === '' ? null : parseFloat(e.target.value) })} />
                        <span>〜</span>
                        <input type="number" className="w-16 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxROI ?? ''} onChange={(e) => onChange({ maxROI: e.target.value === '' ? null : parseFloat(e.target.value) })} />
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">価格(万)</span>
                    <div className="flex items-center gap-1.5">
                        <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minPrice === null ? '' : Math.floor(filters.minPrice / 10000)} onChange={(e) => onChange({ minPrice: e.target.value === '' ? null : parseInt(e.target.value, 10) * 10000 })} />
                        <span>〜</span>
                        <input type="number" className="w-20 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxPrice === null ? '' : Math.floor(filters.maxPrice / 10000)} onChange={(e) => onChange({ maxPrice: e.target.value === '' ? null : parseInt(e.target.value, 10) * 10000 })} />
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">病歴</span>
                    <select className="w-20 border rounded px-2 py-1 h-7 text-xs" value={filters.disease} onChange={(e) => onChange({ disease: e.target.value as Filters['disease'] })}>
                        <option value="any">指定なし</option>
                        <option value="yes">あり</option>
                        <option value="no">なし</option>
                    </select>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">馬体重</span>
                    <div className="flex items-center gap-1.5">
                        <input type="number" className="w-16 border rounded px-2 py-0.5 h-7 text-xs" value={filters.minWeight ?? ''} onChange={(e) => onChange({ minWeight: e.target.value === '' ? null : parseInt(e.target.value, 10) })} />
                        <span>〜</span>
                        <input type="number" className="w-16 border rounded px-2 py-0.5 h-7 text-xs" value={filters.maxWeight ?? ''} onChange={(e) => onChange({ maxWeight: e.target.value === '' ? null : parseInt(e.target.value, 10) })} />
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-700 whitespace-nowrap">繁殖</span>
                    <select className="w-full border rounded px-2 py-1 h-7 text-xs" value={filters.isBroodmare} onChange={(e) => onChange({ isBroodmare: e.target.value as Filters['isBroodmare'] })}>
                        <option value="any">指定なし</option>
                        <option value="yes">繁殖牝馬</option>
                        <option value="no">それ以外</option>
                    </select>
                </div>
            </div>

            <div className="mt-2 flex items-center justify-between">
                <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="h-7 px-3 text-xs" onClick={onExportAll}>
                        全体CSV
                    </Button>
                    <Button variant="outline" size="sm" className="h-7 px-3 text-xs" onClick={onExportFiltered}>
                        絞り込みCSV
                    </Button>
                </div>
                <Button variant="ghost" size="sm" className="h-7 px-2 text-xs text-gray-500 hover:text-gray-700" onClick={onReset}>
                    リセット
                </Button>
            </div>
        </div>
    );
};
