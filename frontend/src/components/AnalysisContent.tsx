'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';

// 通貨をフォーマットするヘルパー関数
const formatCurrency = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === '') return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue) || numValue <= 0) return '-';

  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    maximumFractionDigits: 0
  }).format(numValue);
};

// 価格をフォーマットするヘルパー関数（formatCurrencyのエイリアス）
const formatSoldPrice = (price: number | string | null | undefined, isUnsold: boolean = false): string => {
  if (isUnsold) return '主取り';
  return formatCurrency(price);
};

// 賞金をフォーマットするヘルパー関数
const formatPrize = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === '') return '0.0万円';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue) || numValue <= 0) return '0.0万円';

  const manYen = numValue / 10000;
  return `${manYen.toFixed(1)}万円`;
};

// 性別をフォーマットするヘルパー関数
const formatSex = (sex: string | undefined, isBroodmare: boolean = false) => {
  if (isBroodmare) {
    return { text: '繁', color: 'bg-purple-100 text-purple-700 border-purple-200 font-bold' };
  }
  if (!sex) return { text: '-', color: 'border-gray-200 text-gray-400' };

  switch (sex.toLowerCase()) {
    case '牡':
      return { text: '牡', color: 'border-blue-200 text-blue-500' };
    case '牝':
      return { text: '牝', color: 'border-pink-200 text-pink-500' };
    case 'セ':
      return { text: 'セ', color: 'border-green-200 text-green-600' };
    default:
      return { text: sex, color: 'border-gray-200 text-gray-400' };
  }
};

// 通貨フォーマットのエイリアス
const formatPrice = formatCurrency;

// 日付をフォーマットするヘルパー関数
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(date);
  } catch (e) {
    return '-';
  }
};

import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { useEffect, useState, useMemo, useCallback } from 'react';
import { Horse, AuctionHistory, HorseWithCalculations } from '@/types/horse';
import { getApiBase } from '@/lib/utils';
import { FiltersPanel, Filters } from './analytics/FiltersPanel';
import { FixedSizeList as List } from 'react-window';

const avg = (arr: any[]) => (arr.length ? arr.reduce((a, b) => Number(a) + Number(b), 0) / arr.length : 0);
const median = (arr: any[]) => {
  if (!arr.length) return 0;
  const sorted = [...arr].map(v => Number(v)).sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
};

const initialFilters: Filters = {
  sex: { male: true, female: true, gelding: true },
  minAge: null,
  maxAge: null,
  sire: '',
  minROI: null,
  maxROI: null,
  minPrice: null,
  maxPrice: null,
  disease: 'any',
  minWeight: null,
  maxWeight: null,
  isBroodmare: 'no',
};

// フロントエンドで使用する馬の型（Horse型を拡張）
interface HorseWithAuction extends Horse {
  // フロントエンドで使用する追加プロパティ
  dam_sire: string; // damsireのエイリアス
  detail_url: string; // auction_urlのエイリアス
  comment?: string; // コメント
  weight?: number | null; // 体重
  disease_tags?: string[]; // 疾患タグ
  // オークション情報（将来的な機能拡張用）
  latestAuction?: AuctionHistory;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean;
  auction_date?: string;
  seller?: string;
  // Horseインターフェースのプロパティをオーバーライド
  sold_price?: number | null;
  // その他のプロパティ
  [key: string]: any; // 動的なプロパティに対応
}

interface HorseData {
  horses: Horse[];
  auction_history: AuctionHistory[];
  metadata: {
    total_horses: number;
    total_auctions: number;
    average_price: number;
    last_updated: string;
  };
}

// オークション履歴を馬ごとにグループ化する関数
const groupAuctionHistory = (auctionHistory: AuctionHistory[]): Record<string, AuctionHistory[]> => {
  return auctionHistory.reduce((acc, auction) => {
    const horseId = String(auction.horse_id);
    if (!acc[horseId]) {
      acc[horseId] = [];
    }
    acc[horseId].push(auction);
    return acc;
  }, {} as Record<string, AuctionHistory[]>);
};

function AnalysisContent() {
  const [data, setData] = useState<HorseData | null>(null);
  const [allData, setAllData] = useState<HorseData | null>(null); // 分析サマリー用の全データ
  const [loading, setLoading] = useState(true);
  const [allDataLoading, setAllDataLoading] = useState(true); // 全データローディング状態
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const router = useRouter();
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(50);
  const [total, setTotal] = useState<number>(0);
  const [filters, setFilters] = useState<Filters>(initialFilters);
  const [debugInfo, setDebugInfo] = useState<{ url?: string; ran: boolean; received?: number; total?: number; apiBase?: string; err?: string }>({ ran: false });
  const isDebug = typeof window !== 'undefined' && new URLSearchParams(window.location.search).get('debug') === '1';

  // フィルター処理を最適化（debounce実装）
  const debounce = (fn: (...args: any[]) => void, delay: number) => {
    let timeoutId: NodeJS.Timeout | null = null;
    return (...args: any[]) => {
      if (timeoutId) clearTimeout(timeoutId);
      timeoutId = setTimeout(() => {
        fn(...args);
        timeoutId = null;
      }, delay);
    };
  };

  const debouncedFilterChange = useMemo(() => 
    debounce((next: Partial<Filters>) => {
      setFilters(prev => ({ ...prev, ...next }));
    }, 300), []);
  
  const handleFilterChange = useCallback((next: Partial<Filters>) => debouncedFilterChange(next), [debouncedFilterChange]);
  const handleResetFilters = useCallback(() => debouncedFilterChange(initialFilters), [debouncedFilterChange]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const API_BASE = getApiBase();
      const skip = (page - 1) * limit;
      const url = `${API_BASE}/api/horses?skip=${skip}&limit=${limit}`;
      if (isDebug) { console.log('[AnalysisContent] API_BASE:', API_BASE, 'URL:', url); }
      setDebugInfo({ ran: true, url, apiBase: API_BASE });
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('データの取得に失敗しました');
      const payload = await response.json();
      const horsesData = payload?.horses || [];
      const auctionHistory = payload?.auction_histories || [];

      const horsesWithHistory = horsesData.map((horse: any) => ({
        ...horse,
        latest_auction: null,
        sold_price: horse.sold_price || null,
        is_unsold: horse.is_unsold || false,
        auction_date: horse.auction_date,
        seller: horse.seller,
        weight: horse.weight || null,
        total_prize_start: horse.total_prize_start || 0,
        total_prize_latest: horse.total_prize_latest || 0,
        comment: horse.comment
      } as HorseWithAuction));

      setData({
        horses: horsesWithHistory,
        auction_history: auctionHistory,
        metadata: {
          total_horses: Number(payload?.metadata?.total || horsesWithHistory.length),
          total_auctions: auctionHistory.length,
          average_price: 0,
          last_updated: new Date().toISOString()
        }
      });
      setTotal(Number(payload?.metadata?.total || 0));
      setDebugInfo(prev => ({ ...prev, received: horsesWithHistory.length, total: Number(payload?.metadata?.total || 0) }));
    } catch (e: any) {
      console.error('データ取得エラー:', e);
      setDebugInfo(prev => ({ ...prev, err: String(e?.message || e) }));
      setError('データの読み込みに失敗しました: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  // 分析サマリー用の全データ取得
  const fetchAllData = async () => {
    try {
      setAllDataLoading(true);
      const API_BASE = getApiBase();
      const url = `${API_BASE}/api/horses?skip=0&limit=5000`;
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('全データの取得に失敗しました');
      const payload = await response.json();
      const horsesData = payload?.horses || [];
      const auctionHistory = payload?.auction_histories || [];

      const horsesWithHistory = horsesData.map((horse: any) => {
        // 最新のオークション情報を取得
        const latestAuction = auctionHistory
          .filter((ah: any) => ah.horse_id === horse.id)
          .sort((a: any, b: any) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())[0];

        const horseWithAuction = horse as HorseWithAuction;
        const effectiveWeight = latestAuction?.weight ?? horseWithAuction.weight ?? null;

        const parseDiseaseTags = (tags: any): string[] => {
          if (!tags) return [];
          if (Array.isArray(tags)) return tags;
          if (typeof tags === 'string') {
            const trimmed = tags.trim();
            
            // 空文字や「なし」「特になし」は空配列を返す
            if (!trimmed || trimmed === 'なし' || trimmed === '特になし') {
              return [];
            }
            
            // JSON配列形式の場合
            if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
              try {
                const parsed = JSON.parse(trimmed);
                if (Array.isArray(parsed)) {
                  return parsed.filter(t => typeof t === 'string' && t.trim() !== '');
                }
              } catch (e) {
                // JSONパース失敗時は次の処理へ
              }
            }
            
            // 文字列分割で処理（複数の区切り文字に対応）
            return trimmed.split(/[,;、・]/)
              .map(t => t.trim())
              .filter(t => t !== '' && t !== 'なし' && t !== '特になし');
          }
          return [];
        };

        const parsedDiseaseTags = parseDiseaseTags(horseWithAuction.disease_tags);

        return {
          ...horseWithAuction,
          dam_sire: horseWithAuction.dam_sire || horseWithAuction.damsire || '',
          detail_url: horseWithAuction.detail_url || horseWithAuction.auction_url || '',
          disease_tags: parsedDiseaseTags,
          latestAuction: latestAuction || undefined,
          total_prize_start: latestAuction?.total_prize_start || horseWithAuction.total_prize_start || 0,
          total_prize_latest: latestAuction?.total_prize_latest || horseWithAuction.total_prize_latest || 0,
          is_unsold: latestAuction?.is_unsold || horseWithAuction.is_unsold || false,
          auction_date: latestAuction?.auction_date || horseWithAuction.auction_date || '',
          seller: latestAuction?.seller || horseWithAuction.seller || '',
          sold_price: latestAuction?.sold_price || horseWithAuction.sold_price || 0,
          weight: effectiveWeight
        } as HorseWithAuction;
      });

      setAllData({
        horses: horsesWithHistory,
        auction_history: auctionHistory,
        metadata: {
          total_horses: Number(payload?.metadata?.total || horsesWithHistory.length),
          total_auctions: auctionHistory.length,
          average_price: 0,
          last_updated: new Date().toISOString()
        }
      });
    } catch (e: any) {
      console.error('全データ取得エラー:', e);
    } finally {
      setAllDataLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page, limit]);

  useEffect(() => {
    fetchAllData(); // 分析サマリー用の全データは最初に一度だけ取得
  }, []);

  // 3. データ処理 (Hooksは早期リターンの前に呼び出す必要がある)
  // parseDiseaseTags関数をキャッシュ化してパフォーマンス向上
  const diseaseTagsCache = new Map<string, string[]>();
  
  const parseDiseaseTags = (tags: any): string[] => {
    if (!tags) return [];
    
    // キャッシュチェック
    const cacheKey = typeof tags === 'string' ? tags : JSON.stringify(tags);
    if (diseaseTagsCache.has(cacheKey)) {
      return diseaseTagsCache.get(cacheKey) || [];
    }
    
    let result: string[] = [];
    if (Array.isArray(tags)) {
      result = tags;
    } else if (typeof tags === 'string') {
      const trimmed = tags.trim();
      
      // 空文字や「なし」「特になし」は空配列を返す
      if (!trimmed || trimmed === 'なし' || trimmed === '特になし') {
        result = [];
      } else {
        // JSON配列形式の場合
        if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
          try {
            const parsed = JSON.parse(trimmed);
            if (Array.isArray(parsed)) {
              result = parsed.filter(t => typeof t === 'string' && t.trim() !== '');
            }
          } catch (e) {
            // JSONパース失敗時は次の処理へ
          }
        }
        
        // 文字列分割で処理（複数の区切り文字に対応）
        if (result.length === 0) {
          result = trimmed.split(/[,;、・]/)
            .map(t => t.trim())
            .filter(t => t !== '' && t !== 'なし' && t !== '特になし');
        }
      }
    }
    
    // キャッシュに保存
    diseaseTagsCache.set(cacheKey, result);
    return result;
  };

  const horsesWithLatest = useMemo(() => {
    if (!data) return [];
    return data.horses.map(horse => {
      // 最新のオークション情報を取得
      const latestAuction = data.auction_history
        .filter(ah => ah.horse_id === horse.id)
        .sort((a, b) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())[0];

      const horseWithAuction = horse as HorseWithAuction;
      const effectiveWeight = latestAuction?.weight ?? horseWithAuction.weight ?? null;

      const parsedDiseaseTags = parseDiseaseTags(horseWithAuction.disease_tags);

      return {
        ...horseWithAuction,
        dam_sire: horseWithAuction.dam_sire || horseWithAuction.damsire || '',
        detail_url: horseWithAuction.detail_url || horseWithAuction.auction_url || '',
        disease_tags: parsedDiseaseTags,
        latestAuction: latestAuction || undefined,
        total_prize_start: latestAuction?.total_prize_start || horseWithAuction.total_prize_start || 0,
        total_prize_latest: latestAuction?.total_prize_latest || horseWithAuction.total_prize_latest || 0,
        is_unsold: latestAuction?.is_unsold || horseWithAuction.is_unsold || false,
        auction_date: latestAuction?.auction_date || horseWithAuction.auction_date || '',
        seller: latestAuction?.seller || horseWithAuction.seller || '',
        sold_price: latestAuction?.sold_price || horseWithAuction.sold_price || 0,
        weight: effectiveWeight
      };
    });
  }, [data]);

  const horses = horsesWithLatest;

  const sireSuggestions = useMemo(() => Array.from(new Set((allData?.horses as HorseWithAuction[] || []).map(h => h.sire).filter(Boolean))), [allData]);

  const filteredHorsesList = useMemo(() => {
    if (!allData || allData.horses.length === 0) return [];
    return (allData.horses as HorseWithAuction[]).filter((h: HorseWithAuction) => {
      if (h.sex === '牡' && !filters.sex.male) return false;
      if (h.sex === '牝' && !filters.sex.female) return false;
      if (h.sex === 'セ' && !filters.sex.gelding) return false;
      const age = h.age ?? 0;
      if (filters.minAge !== null && age < filters.minAge) return false;
      if (filters.maxAge !== null && age > filters.maxAge) return false;
      if (filters.sire && !h.sire?.toLowerCase().includes(filters.sire.toLowerCase())) return false;
      const earnedPrize = (h.total_prize_latest || 0) - (h.total_prize_start || 0);
      const soldPrice = Number(h.sold_price || 0);
      const roi = soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;
      if (filters.minROI !== null && roi < filters.minROI) return false;
      if (filters.maxROI !== null && roi > filters.maxROI) return false;
      if (filters.minPrice !== null && soldPrice < filters.minPrice) return false;
      if (filters.maxPrice !== null && soldPrice > filters.maxPrice) return false;
      const hasDisease = Array.isArray(h.disease_tags) && h.disease_tags.length > 0;
      if (filters.disease === 'yes' && !hasDisease) return false;
      if (filters.disease === 'no' && hasDisease) return false;
      const w = h.weight ?? 0;
      if (w > 0) {
        if (filters.minWeight !== null && w < filters.minWeight) return false;
        if (filters.maxWeight !== null && w > filters.maxWeight) return false;
      } else if (filters.minWeight !== null && filters.minWeight > 0) {
        return false;
      }
      if (filters.isBroodmare === 'yes' && !h.is_broodmare) return false;
      if (filters.isBroodmare === 'no' && h.is_broodmare) return false;
      return true;
    });
  }, [allData, filters]);

  const stats = useMemo(() => {
    if (filteredHorsesList.length === 0) {
      return { count: 0, avgPrice: 0, medianPrice: 0, avgROI: 0, medianROI: 0, avgWeight: 0, medianWeight: 0, avgAge: 0, avgPrizeStart: 0, medianPrizeStart: 0, avgPrizeLatest: 0, medianPrizeLatest: 0, diseaseCount: 0, sexGroups: {} };
    }
    const prices = filteredHorsesList.filter((h: HorseWithAuction) => !h.is_unsold).map((h: HorseWithAuction) => Number(h.sold_price || 0));
    const prizeStarts = filteredHorsesList.map((h: HorseWithAuction) => Number(h.total_prize_start || 0));
    const prizeLatests = filteredHorsesList.map((h: HorseWithAuction) => Number(h.total_prize_latest || 0));
    const rois = filteredHorsesList.map((h: HorseWithAuction) => {
      const earnedPrize = (h.total_prize_latest || 0) - (h.total_prize_start || 0);
      const soldPrice = Number(h.sold_price || 0);
      return soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;
    });
    const weights = filteredHorsesList.map((h: HorseWithAuction) => Number(h.weight || 0)).filter((w: number) => w > 0);
    const sexGroups = filteredHorsesList.reduce((acc: any, h: HorseWithAuction) => {
      const sex = h.sex || '不明';
      if (!acc[sex]) acc[sex] = [];
      acc[sex].push(h);
      return acc;
    }, {} as Record<string, HorseWithAuction[]>);
    return {
      count: filteredHorsesList.length,
      avgPrice: avg(prices),
      medianPrice: median(prices),
      avgROI: avg(rois),
      medianROI: median(rois),
      avgWeight: avg(weights),
      medianWeight: median(weights),
      avgAge: avg(filteredHorsesList.map((h: HorseWithAuction) => Number(h.age || 0))),
      avgPrizeStart: avg(prizeStarts),
      medianPrizeStart: median(prizeStarts),
      avgPrizeLatest: avg(prizeLatests),
      medianPrizeLatest: median(prizeLatests),
      diseaseCount: filteredHorsesList.filter((h: HorseWithAuction) => h.disease_tags && h.disease_tags.length > 0).length,
      sexGroups,
    };
  }, [filteredHorsesList]);


  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  if (error || !data) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error || 'データがありません'}</div>;
  }

  // CSVエクスポートユーティリティ
  const toCsv = (rows: any[]) => {
    const headers = ['ID', '馬名', '性別', '年齢', '父', '馬体重', '落札価格', '落札時賞金', '現在賞金', 'ROI', 'リンク', '病歴', '繁殖'];
    const escape = (v: any) => {
      if (v === null || v === undefined) return '';
      const s = String(v);
      if (s.includes('"') || s.includes(',') || s.includes('\n')) return '"' + s.replace(/"/g, '""') + '"';
      return s;
    };
    const lines = [headers.join(',')];
    for (const h of rows) {
      const disease = Array.isArray(h.disease_tags) ? h.disease_tags.join(' / ') : (h.disease_tags ?? '');
      const earnedPrize = (h.total_prize_latest || 0) - (h.total_prize_start || 0);
      const soldPrice = Number(h.sold_price || 0);
      const roi = soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;
      const row = [String(h.id), h.name ?? '', h.sex ?? '', h.age ?? '', h.sire ?? '', h.weight ?? '', soldPrice, h.total_prize_start ?? '', h.total_prize_latest ?? '', roi.toFixed(2), h.detail_url || h.auction_url || '', disease, h.is_broodmare ? '○' : ''].map(escape).join(',');
      lines.push(row);
    }
    return '\uFEFF' + lines.join('\n');
  };

  const downloadCsv = (filename: string, content: string) => {
    const blob = new Blob([content], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleExportAll = () => downloadCsv('horses_all.csv', toCsv(allData?.horses as HorseWithAuction[] || []));
  const handleExportFiltered = () => downloadCsv('horses_filtered.csv', toCsv(filteredHorsesList));

  const DebugOverlay = () => !isDebug ? null : (
    <div style={{ position: 'fixed', top: 8, right: 8, zIndex: 9999 }}>
      <div style={{ background: '#111827', color: '#e5e7eb', padding: '8px 10px', borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,0.2)', maxWidth: 360 }}>
        <div style={{ fontWeight: 600, marginBottom: 4 }}>Debug</div>
        <div style={{ fontSize: 12, lineHeight: 1.4 }}>
          <div>API_BASE: <code>{debugInfo.apiBase || '(empty)'}</code></div>
          <div>URL: <code style={{ wordBreak: 'break-all' }}>{debugInfo.url}</code></div>
          <div>ran: {String(debugInfo.ran)} / received: {debugInfo.received ?? '-'} / total: {debugInfo.total ?? '-'}</div>
          {debugInfo.err && <div style={{ color: '#fca5a5' }}>error: {debugInfo.err}</div>}
        </div>
      </div>
    </div>
  );

  // 仮想化された行コンポーネント
  const VirtualizedRow = ({ index, style }: { index: number; style: React.CSSProperties }) => {
    const horse = tableHorses[index];
    return (
      <div style={style} className="flex items-center border-b border-gray-200 hover:bg-blue-50/50 transition-colors">
        <div className="flex items-center px-3 py-2 text-sm" style={{ width: '1100px' }}>
          <div className="w-48 pr-2 text-left">{horse.name ? (
            <Link href={`/horses/${horse.id}`} className="font-medium text-blue-600 hover:text-blue-800 hover:underline">
              {horse.name}
            </Link>
          ) : '-'}</div>
          <div className="w-16 text-center">
            {(() => {
              const sexInfo = formatSex(horse.sex, horse.is_broodmare);
              return (
                <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${sexInfo.color}`}>
                  {sexInfo.text}
                </span>
              );
            })()}
          </div>
          <div className="w-12 text-center text-gray-600">{displayAge(horse.age)}</div>
          <div className="w-32 text-center text-gray-600 truncate">{horse.sire || '-'}</div>
          <div className="w-20 text-center text-gray-600 pr-2">{horse.weight || '-'}</div>
          <div className="w-24 text-center text-gray-700 font-medium pr-2">
            {displayPrice(horse.sold_price, horse.is_unsold)}
          </div>
          <div className="w-24 text-center text-gray-600 pr-4">
            {formatPrize(horse.total_prize_start)}
          </div>
          <div className="w-24 text-center text-gray-600 pr-4">
            {formatPrize(horse.total_prize_latest)}
          </div>
          <div className="w-20 text-center font-semibold text-gray-700 pr-2">
            {calcROI(horse.total_prize_latest, horse.total_prize_start, horse.sold_price)}
          </div>
          <div className="w-16 text-center">
            {(() => {
              const hasDisease = Array.isArray(horse.disease_tags) && horse.disease_tags.length > 0;
              return hasDisease ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-red-50 text-red-600 border border-red-100">
                  あり
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold bg-blue-50 text-blue-500 border border-blue-100">
                  なし
                </span>
              );
            })()}
          </div>
          <div className="w-20 text-center">
            <div className="flex gap-2 justify-center">
              {horse.jbis_url && (
                <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-gray-400 hover:text-blue-600 underline">JBIS</a>
              )}
              {(horse.detail_url || horse.auction_url) && (
                <a href={horse.detail_url || horse.auction_url} target="_blank" rel="noopener noreferrer" className="text-[10px] text-gray-400 hover:text-blue-600 underline">サラ</a>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  };

  // 表示リスト
  let tableHorses: HorseWithAuction[] = [...filteredHorsesList];

  // 年齢を表示するヘルパー関数
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return String(age);
  };

  // 落札価格を表示するヘルパー関数
  const displayPrice = formatSoldPrice;

  // 賞金を表示するヘルパー関数
  const displayPrize = formatPrize;

  // ROIを計算するヘルパー関数
  const calcROI = (prizeLatest: number | undefined, prizeStart: number | undefined, price: number | string | null | undefined): string => {
    if (prizeLatest === undefined || prizeStart === undefined || !price) return '-';
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    if (isNaN(numPrice) || numPrice <= 0) return '-';
    const earnedPrize = prizeLatest - prizeStart;
    if (numPrice <= 0) return '-';
    const rio = (earnedPrize * 10000) / numPrice;
    return (rio * 100).toFixed(1) + '%';
  };

  // ソート関数の型定義
  type SortFunction = (a: HorseWithAuction, b: HorseWithAuction) => number;
  const sortFunctions: Record<string, SortFunction> = {
    name: (a, b) => (a?.name ?? '').localeCompare(b?.name ?? '', 'ja'),
    sex: (a, b) => (a?.sex ?? '').localeCompare(b?.sex ?? '', 'ja'),
    weight: (a, b) => (a?.weight ?? 0) - (b?.weight ?? 0),
    age: (a, b) => {
      const ageA = typeof a?.age === 'number' ? a.age : (a?.age ? parseFloat(String(a.age)) : 0);
      const ageB = typeof b?.age === 'number' ? b.age : (b?.age ? parseFloat(String(b.age)) : 0);
      return ageA - ageB;
    },
    sire: (a, b) => (a?.sire ?? '').localeCompare(b?.sire ?? '', 'ja'),
    sold_price: (a, b) => {
      const getPrice = (p: any, isUnsold: boolean = false) => {
        if (isUnsold) return 0;
        if (p === null || p === undefined) return 0;
        if (typeof p === 'number') return p;
        return parseFloat(String(p).replace(/[^0-9.]/g, '')) || 0;
      };
      return getPrice(a.sold_price, a.is_unsold) - getPrice(b.sold_price, b.is_unsold);
    },
    total_prize_start: (a, b) => (a.total_prize_start || 0) - (b.total_prize_start || 0),
    total_prize_latest: (a, b) => (a.total_prize_latest || 0) - (b.total_prize_latest || 0),
    roi: (a, b) => {
      const getPrice = (p: any, isUnsold: boolean = false) => {
        if (isUnsold) return 0;
        if (p === null || p === undefined) return 0;
        if (typeof p === 'number') return p;
        return parseFloat(String(p).replace(/[^0-9.]/g, '')) || 0;
      };
      const aPrice = getPrice(a.sold_price, a.is_unsold);
      const bPrice = getPrice(b.sold_price, b.is_unsold);
      const aEarnedPrize = (a.total_prize_latest || 0) - (a.total_prize_start || 0);
      const bEarnedPrize = (b.total_prize_latest || 0) - (b.total_prize_start || 0);
      const aROI = aPrice > 0 ? (aEarnedPrize * 10000) / aPrice : 0;
      const bROI = bPrice > 0 ? (bEarnedPrize * 10000) / bPrice : 0;
      return aROI - bROI;
    },
    disease: (a, b) => {
      const isNoDiseaseA = (tags: any) => {
        if (!tags) return true;
        const negativeTags = ['なし', 'なし。', '特になし', '特になし。', 'なし（特記事項なし）', '疾患履歴なし'];
        if (Array.isArray(tags)) return tags.length === 0 || tags.every(t => negativeTags.includes(String(t).trim()));
        return negativeTags.includes(String(tags).trim());
      };
      const aNo = isNoDiseaseA(a.disease_tags);
      const bNo = isNoDiseaseA(b.disease_tags);
      if (aNo === bNo) return 0;
      return aNo ? 1 : -1;
    }
  };

  // ソートハンドラ
  const handleSort = useCallback((key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder(key === 'name' ? 'asc' : 'desc');
    }
  }, [sortKey, sortOrder]);

  // ソートアイコン
  const renderSortIcon = (key: string) => {
    if (sortKey !== key) return <FaSort className="inline ml-1 text-gray-400" />;
    return sortOrder === 'asc' ? <FaSortUp className="inline ml-1 text-blue-600" /> : <FaSortDown className="inline ml-1 text-blue-600" />;
  };

  // ソート処理を適用
  if (sortKey && sortFunctions[sortKey]) {
    tableHorses = [...tableHorses].sort((a, b) => {
      const res = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? res : -res;
    });
  }

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <DebugOverlay />
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col lg:flex-row gap-6">
          <div className="flex-1 min-w-0">
            {/* フィルターパネル */}
            <FiltersPanel
              filters={filters}
              onChange={handleFilterChange}
              onReset={handleResetFilters}
              sireSuggestions={sireSuggestions}
              onExportAll={handleExportAll}
              onExportFiltered={handleExportFiltered}
              className="mb-6"
            />


            {/* 馬テーブル - 仮想化 */}
            <div className="bg-white rounded-lg shadow border overflow-x-auto">
              {/* テーブルヘッダー */}
              <div className="bg-gray-50 border-b border-gray-200 min-w-max">
                <div className="flex items-center px-3 py-3 text-xs font-semibold text-gray-600 uppercase tracking-wider" style={{ width: '1100px' }}>
                  <div className="w-48 cursor-pointer pr-2 text-left" onClick={() => handleSort('name')}>馬名{renderSortIcon('name')}</div>
                  <div className="w-16 text-center cursor-pointer" onClick={() => handleSort('sex')}>性別{renderSortIcon('sex')}</div>
                  <div className="w-12 text-center cursor-pointer" onClick={() => handleSort('age')}>年齢{renderSortIcon('age')}</div>
                  <div className="w-32 text-center cursor-pointer" onClick={() => handleSort('sire')}>父{renderSortIcon('sire')}</div>
                  <div className="w-20 text-center cursor-pointer pr-2" onClick={() => handleSort('weight')}>馬体重{renderSortIcon('weight')}</div>
                  <div className="w-24 text-center cursor-pointer pr-2" onClick={() => handleSort('sold_price')}>落札価格{renderSortIcon('sold_price')}</div>
                  <div className="w-24 text-center pr-4">落札時</div>
                  <div className="w-24 text-center pr-4">現在</div>
                  <div className="w-20 text-center pr-2">ROI</div>
                  <div className="w-16 text-center cursor-pointer" onClick={() => handleSort('disease')}>病歴{renderSortIcon('disease')}</div>
                  <div className="w-20 text-center">リンク</div>
                </div>
              </div>
              
              {/* 仮想化されたテーブル本体 */}
              {loading || allDataLoading ? (
                <div className="text-center py-10 text-gray-500">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-3"></div>
                  <div>{loading ? 'データを読み込み中...' : '分析データを準備中...'}</div>
                </div>
              ) : tableHorses.length === 0 ? (
                <div className="text-center py-10 text-gray-500 italic">
                  該当する馬が見つかりませんでした。フィルター設定を見直してください。
                </div>
              ) : (
                <div style={{ height: Math.min(tableHorses.length * 50, 600), width: '1100px' }}>
                  <List
                    width="100%"
                    height={Math.min(tableHorses.length * 50, 600)}
                    itemCount={tableHorses.length}
                    itemSize={50}
                    itemData={tableHorses}
                  >
                    {VirtualizedRow}
                  </List>
                </div>
              )}
            </div>

            {/* ページネーション */}
            <div className="mt-6 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                ページ {page} / {Math.max(1, Math.ceil((total || 0) / limit))}（{(page - 1) * limit + 1} - {Math.min(page * limit, total || page * limit)} 件 / 全{total}件）
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1 || loading}>前へ</Button>
                <Button variant="outline" size="sm" onClick={() => setPage(p => (p * limit < (total || 0) ? p + 1 : p))} disabled={page * limit >= (total || 0) || loading}>次へ</Button>
              </div>
            </div>
          </div>

          {/* 統計サイドバー */}
          <aside className="w-full lg:w-72 flex flex-col gap-6">
            <Card className="shadow-sm border-gray-200">
              <CardHeader className="py-4 border-b bg-gray-50/50">
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                  <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                  分析サマリー
                </CardTitle>
              </CardHeader>
              <CardContent className="p-4 space-y-5">
                <div>
                  <div className="text-[11px] text-gray-400 uppercase font-bold tracking-wider mb-1">対象馬数</div>
                  <div className="text-2xl font-black text-gray-800">{stats.count.toLocaleString()}<span className="text-xs font-normal ml-1 text-gray-500">頭</span></div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">平均落札価格</div>
                    <div className="text-sm font-bold text-gray-700">{Math.round(stats.avgPrice / 10000).toLocaleString()}<span className="text-[10px] font-normal ml-0.5">万</span></div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">中央値</div>
                    <div className="text-sm font-bold text-gray-700">{Math.round(stats.medianPrice / 10000).toLocaleString()}<span className="text-[10px] font-normal ml-0.5">万</span></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-100">
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">平均ROI</div>
                    <div className="text-sm font-bold text-green-600">{stats.avgROI.toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">中央値</div>
                    <div className="text-sm font-bold text-green-600">{stats.medianROI.toFixed(1)}%</div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-100">
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">平均落札時賞金</div>
                    <div className="text-sm font-bold text-gray-700">{(stats.avgPrizeStart / 10000).toFixed(2)}<span className="text-[10px] font-normal ml-0.5">万</span></div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">中央値</div>
                    <div className="text-sm font-bold text-gray-700">{(stats.medianPrizeStart / 10000).toFixed(2)}<span className="text-[10px] font-normal ml-0.5">万</span></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-100">
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">平均現在賞金</div>
                    <div className="text-sm font-bold text-gray-700">{(stats.avgPrizeLatest / 10000).toFixed(2)}<span className="text-[10px] font-normal ml-0.5">万</span></div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">中央値</div>
                    <div className="text-sm font-bold text-gray-700">{(stats.medianPrizeLatest / 10000).toFixed(2)}<span className="text-[10px] font-normal ml-0.5">万</span></div>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2 border-t border-gray-100">
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">平均馬体重</div>
                    <div className="text-sm font-bold text-gray-700">{Math.round(stats.avgWeight)}<span className="text-[10px] font-normal ml-0.5">kg</span></div>
                  </div>
                  <div>
                    <div className="text-[10px] text-gray-400 uppercase font-bold mb-1">平均年齢</div>
                    <div className="text-sm font-bold text-gray-700">{stats.avgAge.toFixed(1)}<span className="text-[10px] font-normal ml-0.5">歳</span></div>
                  </div>
                </div>

                <div className="pt-2 border-t border-gray-100">
                  <div className="text-[10px] text-gray-400 uppercase font-bold mb-2">性別内訳</div>
                  <div className="space-y-1.5">
                    {(['牡', '牝', 'セ'] as const).map(sex => {
                      const group = stats.sexGroups[sex] || [];
                      const percentage = stats.count > 0 ? (group.length / stats.count) * 100 : 0;
                      return (
                        <div key={sex} className="flex items-center justify-between text-xs">
                          <span className="text-gray-500">{sex}</span>
                          <div className="flex items-center gap-2 flex-1 mx-3">
                            <div className="h-1.5 flex-1 bg-gray-100 rounded-full overflow-hidden">
                              <div className={`h-full ${sex === '牡' ? 'bg-blue-400' : sex === '牝' ? 'bg-pink-400' : 'bg-green-400'}`} style={{ width: `${percentage}%` }}></div>
                            </div>
                          </div>
                          <span className="font-bold text-gray-700 w-8 text-right">{group.length}</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </CardContent>
            </Card>

            <div className="bg-amber-50 border border-amber-100 rounded-lg p-4">
              <div className="text-xs font-bold text-amber-800 mb-1 flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                ヒント
              </div>
              <p className="text-[11px] text-amber-700 leading-relaxed">
                フィルタを適用するとサイドバーの統計もリアルタイムに更新されます。特定の条件下での落札成功率やROI分析にご活用ください。
              </p>
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}

export default React.memo(AnalysisContent);
