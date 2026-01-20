'use client';

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

// フォーマット関数をインポート
import { formatPrice, formatPrize } from '@/utils/format';

// normalize.ts から formatSex と getSexColor をインポート
import { formatSex, getSexColor } from '@/utils/normalize';

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

import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { Horse, AuctionHistory, HorseWithCalculations } from '@/types/horse';
import { HorseTable } from './horses/HorseTable';
import { FiltersPanel, type Filters } from '@/components/analytics/FiltersPanel';

// HorseWithCalculations 型を使用

interface HorseData {
  horses: Horse[];
  auction_histories: AuctionHistory[];
  metadata: {
    total: number;
    count: number;
    total_auctions?: number;
    average_price?: number;
    last_updated?: string;
    total_horses?: number; // 後方互換性のため
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

const DEFAULT_FILTERS: Filters = {
  sex: { male: true, female: true, gelding: true, broodmare: false },
  minAge: 0,
  maxAge: 30,
  sire: '',
  // 未入力（null）はフィルタ無効を意味する
  minROI: null,
  maxROI: null,
  minPrice: null,
  maxPrice: null,
  disease: 'any',
  minWeight: null,
  maxWeight: null,
};

export default function AnalysisContent() {
  const [horses, setHorses] = useState<HorseWithCalculations[]>([]);
  const [filteredHorses, setFilteredHorses] = useState<HorseWithCalculations[]>([]);
  // オークション履歴は使用しないため削除
  // setAuctionHistory は使用しないため削除
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{
    total: number;
    count: number;
    total_auctions?: number;
    average_price?: number;
    last_updated?: string;
    total_horses?: number; // 後方互換性のため
  }>({
    total: 0,
    count: 0,
    total_auctions: 0,
    average_price: 0,
    last_updated: new Date().toISOString(),
  });
  const [sortKey, setSortKey] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const router = useRouter();
  const [filters, setFilters] = useState<Filters>({ ...DEFAULT_FILTERS });
  const [page, setPage] = useState<number>(1);
  const [limit, setLimit] = useState<number>(50);
  const [total, setTotal] = useState<number>(0);
  // 入力ボックス用と送信用の状態を分離
  const [searchInput, setSearchInput] = useState<string>('');
  const [search, setSearch] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8001';
        const skip = (page - 1) * limit;
        const sortParam = sortKey === 'sold_price' ? (sortOrder === 'asc' ? 'price_asc' : 'price_desc')
          : sortKey === 'name' ? (sortOrder === 'asc' ? 'name_asc' : 'name_desc')
            : 'price_desc';
        // 馬データを取得（ページネーション）
        console.log('馬データの取得を開始します...');
        // 検索パラメータ（数値のみの場合は id、文字列は q）
        const trimmed = search.trim();
        const isIdSearch = /^\d+$/.test(trimmed);
        const idParam = trimmed && isIdSearch ? `&id=${encodeURIComponent(trimmed)}` : '';
        const qParamFromSearch = trimmed && !isIdSearch ? `&q=${encodeURIComponent(trimmed)}` : '';

        // フィルタをサーバー側へ渡す（全体データに対する絞り込み）
        const sexValues: string[] = [];
        if (filters.sex.male) sexValues.push('牡');
        if (filters.sex.female || filters.sex.broodmare) sexValues.push('牝');
        if (filters.sex.gelding) sexValues.push('セ');
        const sexParam = sexValues.length > 0 && sexValues.length < 3
          ? `&sex=${encodeURIComponent(sexValues.join(','))}`
          : '';

        const minAgeParam = filters.minAge && filters.minAge > 0 ? `&min_age=${filters.minAge}` : '';
        const maxAgeParam = (typeof filters.maxAge === 'number' && filters.maxAge < 30) ? `&max_age=${filters.maxAge}` : '';

        const minPriceParam = filters.minPrice != null ? `&min_price=${filters.minPrice}` : '';
        const maxPriceParam = filters.maxPrice != null ? `&max_price=${filters.maxPrice}` : '';

        const minWeightParam = filters.minWeight != null ? `&min_weight=${filters.minWeight}` : '';
        const maxWeightParam = filters.maxWeight != null ? `&max_weight=${filters.maxWeight}` : '';

        const minRoiParam = filters.minROI != null ? `&min_roi=${filters.minROI}` : '';
        const maxRoiParam = filters.maxROI != null ? `&max_roi=${filters.maxROI}` : '';

        // sireが入力されている場合は q にも反映（既にsearchが文字列のときはsearch優先）
        const qParamFromSire = (!trimmed && filters.sire) ? `&q=${encodeURIComponent(filters.sire)}` : '';

        const url = `${apiBaseUrl}/api/horses?skip=${skip}&limit=${limit}&sort=${encodeURIComponent(sortParam)}${idParam}${qParamFromSearch}${sexParam}${minAgeParam}${maxAgeParam}${minPriceParam}${maxPriceParam}${minWeightParam}${maxWeightParam}${minRoiParam}${maxRoiParam}${qParamFromSire}`;
        const response = await fetch(url, {
          cache: 'no-store',
          headers: {
            'Content-Type': 'application/json',
          }
        });

        console.log('APIリクエスト完了:', response.status, response.statusText);

        if (!response.ok) {
          let errorData;
          try {
            errorData = await response.json();
            console.error('APIエラーレスポンス:', {
              status: response.status,
              statusText: response.statusText,
              errorData,
              url: response.url
            });
          } catch (jsonError) {
            console.error('エラーレスポンスの解析に失敗しました:', jsonError);
          }
          throw new Error(`データの取得に失敗しました: ${response.status} ${response.statusText}`);
        }

        const responseData = await response.json();
        console.log('APIレスポンスを受信しました:', responseData);
        const list = Array.isArray(responseData) ? responseData : (responseData?.horses || []);
        const apiTotal = Number(responseData?.metadata?.total || list.length || 0);
        setTotal(apiTotal);

        console.log(`馬データを取得しました: ${list.length}件 / 総数: ${apiTotal}`);

        const horsesWithAuction = list.map((horse: any) => {
          const mappedHorse = {
            ...horse,
            dam_sire: horse.dam_sire || '',
            detail_url: horse.detail_url || '',
            jbis_url: horse.jbis_url || horse.jbisUrl || '', // jbis_url または jbisUrl のいずれかが存在する場合に設定
            comment: horse.comment,
            race_record: horse.race_record
          };

          // デバッグ用: 最初の数件の馬データをログに出力
          if (horse.id <= 5) {
            console.log(`馬ID: ${horse.id}, 名前: ${horse.name}, jbis_url: ${mappedHorse.jbis_url}`);
          }

          return mappedHorse;
        });

        setHorses(horsesWithAuction);
        // メタデータを更新
        const newMetadata = {
          total: apiTotal,
          count: list.length,
          total_auctions: 0,
          average_price: 0,
          last_updated: new Date().toISOString(),
          total_horses: apiTotal
        };

        setMetadata(newMetadata);

        // オークション履歴は使用しないため空のオブジェクトを設定
        const auctionHistoryByHorseId: Record<string, any[]> = {};

        // 馬データにオークション情報をマージ
        const horsesWithHistory = horsesWithAuction.map((horse: HorseWithCalculations) => {
          // デバッグ用: ホワイトアッシュのデータをログに出力
          if (horse.name === 'ホワイトアッシュ') {
            console.log('ホワイトアッシュのデータ:', {
              horseData: horse,
              auctionHistory: auctionHistoryByHorseId[horse.id],
              latestAuction: horse.latestAuction || (auctionHistoryByHorseId[horse.id] || [])[0]
            });
          }
          // 既存のオークション情報を保持
          const latestAuction = horse.latestAuction || (auctionHistoryByHorseId[horse.id] || [])[0];

          // 馬の基本情報を保持しつつ、オークション情報をマージ
          return {
            ...horse,
            latestAuction: latestAuction || null,
            latest_auction: latestAuction || null,
            // sold_price は horse オブジェクトから直接取得
            sold_price: horse.sold_price !== undefined ? horse.sold_price : (latestAuction?.sold_price || null),
            // is_unsold も horse オブジェクトから直接取得
            is_unsold: horse.is_unsold !== undefined ? horse.is_unsold : (latestAuction?.is_unsold || false),
            auction_date: latestAuction?.auction_date || horse.auction_date,
            seller: latestAuction?.seller || horse.seller,
            weight: latestAuction?.weight ?? horse.weight ?? null,
            total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start,
            total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest,
            comment: latestAuction?.comment || horse.comment,
            race_record: horse.race_record
          } as HorseWithCalculations;
        });

        // データを状態に保存
        setHorses(horsesWithHistory);
        setMetadata(newMetadata);
        setLoading(false);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : '不明なエラー';
        console.error('データ取得エラー:', error);
        setError(`データの取得中にエラーが発生しました: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [page, limit, sortKey, sortOrder, search, filters]);

  // フックは早期returnの前に呼び出す必要がある
  const sireSuggestions = useMemo(() => {
    return horses.map(h => h.sire).filter(Boolean) as string[];
  }, [horses]);

  const isFiltered = useMemo(() => {
    return JSON.stringify(filters) !== JSON.stringify(DEFAULT_FILTERS);
  }, [filters]);

  // CSVエクスポートユーティリティ
  const toCsv = (rows: any[]) => {
    const headers = [
      '馬名', '性別', '年齢', '父', '馬体重', '落札価格', '落札時賞金', '現在賞金', 'ROI', 'リンク', '病歴'
    ];
    const escape = (v: any) => {
      if (v === null || v === undefined) return '';
      const s = String(v);
      if (s.includes('"') || s.includes(',') || s.includes('\n')) {
        return '"' + s.replace(/"/g, '""') + '"';
      }
      return s;
    };
    const lines = [headers.join(',')];
    for (const h of rows) {
      const disease = Array.isArray((h as any).disease_tags)
        ? (h as any).disease_tags.join(' / ')
        : ((h as any).disease_tags ?? '');
      const link = h.detail_url || h.auction_url || '';
      const weightVal = h.weight ?? h.display_weight ?? '';
      const soldPrice = typeof h.sold_price === 'number' ? h.sold_price : (h.price ?? '');
      const row = [
        h.name ?? '',
        h.sex ?? '',
        h.age ?? '',
        h.sire ?? '',
        weightVal,
        soldPrice,
        h.total_prize_start ?? '',
        h.total_prize_latest ?? '',
        typeof h.roi === 'number' ? h.roi : h.display_roi ?? '',
        link,
        disease,
      ].map(escape).join(',');
      lines.push(row);
    }
    // UTF-8 BOM を付与
    const csvContent = '\uFEFF' + lines.join('\n');
    return csvContent;
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

  const handleExportAll = () => {
    const csv = toCsv(horses);
    downloadCsv('horses_all.csv', csv);
  };

  const handleExportFiltered = () => {
    const csv = toCsv(filteredHorsesList);
    downloadCsv('horses_filtered.csv', csv);
  };

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  if (error || !horses.length) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error || 'データがありません'}</div>;
  }

  const hasDisease = (tags: any): boolean => {
    if (tags === undefined || tags === null || tags === '') return false;
    if (Array.isArray(tags)) {
      if (tags.length === 0) return false;
      return !tags.every(tag => {
        const strTag = String(tag).trim();
        return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
      });
    }
    const strTag = String(tags).trim();
    return !(strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。');
  };

  const calcROIValue = (h: HorseWithCalculations): number => {
    const sold = typeof h.sold_price === 'number' ? h.sold_price : 0;
    const start = h.total_prize_start || 0;
    const latest = h.total_prize_latest || 0;
    const earned = latest - start;
    if (!sold || sold <= 0) return 0;
    return (earned * 10000) / sold;
  };

  const inSex = (h: HorseWithCalculations): boolean => {
    const s = String(h.sex || '');
    const isBroodmare = !!h.is_broodmare;

    const okMale = filters.sex.male && s.includes('牡');
    const okGelding = filters.sex.gelding && s.includes('セ');

    // 牝馬の判定（繁殖牝馬でないもの）
    const okFemale = filters.sex.female && s.includes('牝') && !isBroodmare;

    // 繁殖牝馬の判定
    const okBroodmare = filters.sex.broodmare && isBroodmare;

    return okMale || okFemale || okGelding || okBroodmare;
  };

  const inAge = (h: HorseWithCalculations): boolean => {
    const a = typeof h.age === 'number' ? h.age : (h.age ? parseFloat(String(h.age)) : NaN);
    if (Number.isNaN(a)) return true;
    return a >= filters.minAge && a <= filters.maxAge;
  };

  const inSire = (h: HorseWithCalculations): boolean => {
    if (!filters.sire) return true;
    const lhs = String(h.sire || '').normalize('NFC').toLowerCase();
    const rhs = String(filters.sire).normalize('NFC').toLowerCase();
    return lhs.includes(rhs);
  };

  const inPrice = (h: HorseWithCalculations): boolean => {
    const p = typeof h.sold_price === 'number' ? h.sold_price : 0;
    if (filters.minPrice && p < filters.minPrice) return false;
    if (filters.maxPrice && filters.maxPrice > 0 && p > filters.maxPrice) return false;
    return true;
  };

  const inROI = (h: HorseWithCalculations): boolean => {
    const r = calcROIValue(h);
    if (filters.minROI && r < filters.minROI) return false;
    if (filters.maxROI && filters.maxROI > 0 && r > filters.maxROI) return false;
    return true;
  };

  const inDisease = (h: HorseWithCalculations): boolean => {
    if (filters.disease === 'any') return true;
    const has = hasDisease((h as any).disease_tags);
    return filters.disease === 'yes' ? has : !has;
  };

  const inWeight = (h: HorseWithCalculations): boolean => {
    const w = h.weight == null ? NaN : (typeof h.weight === 'number' ? h.weight : parseFloat(String(h.weight)));
    if (Number.isNaN(w)) return true;
    if (filters.minWeight && w < filters.minWeight) return false;
    if (filters.maxWeight && filters.maxWeight > 0 && w > filters.maxWeight) return false;
    return true;
  };

  const filteredHorsesList = horses
    .filter(inSex)
    .filter(inAge)
    .filter(inSire)
    .filter(inPrice)
    .filter(inROI)
    .filter(inDisease)
    .filter(inWeight);

  // ソート
  if (sortKey) {
    filteredHorsesList.sort((a: HorseWithCalculations, b: HorseWithCalculations) => {
      let aValue = (a as any)[sortKey];
      let bValue = (b as any)[sortKey];

      // 価格の特別な処理
      if (sortKey === 'sold_price') {
        // 文字列の場合はカンマを削除して数値に変換
        const parsePrice = (price: any): number => {
          if (price === null || price === undefined) return 0;
          if (typeof price === 'number') return price;
          if (typeof price === 'string') {
            // カンマを削除して数値に変換
            const cleanPrice = price.replace(/[^0-9.-]+/g, '');
            return parseFloat(cleanPrice) || 0;
          }
          return 0;
        };

        aValue = parsePrice(aValue);
        bValue = parsePrice(bValue);
      } else {
        // その他のフィールドの処理
        aValue = aValue || 0;
        bValue = bValue || 0;

        // 数値に変換
        if (typeof aValue === 'string') aValue = parseFloat(aValue) || 0;
        if (typeof bValue === 'string') bValue = parseFloat(bValue) || 0;
      }

      return sortOrder === 'asc'
        ? (aValue as number) - (bValue as number)
        : (bValue as number) - (aValue as number);
    });
  }

  // サマリー - RIO計算を詳細ページと合わせる
  const avgRIO = horses.length > 0 ? (
    horses.reduce((sum, h) => {
      let soldPrice = 0;
      const price = h.sold_price;

      // sold_priceの型を安全に処理
      if (price !== null && price !== undefined) {
        if (typeof price === 'number') {
          soldPrice = price;
        } else if (typeof price === 'string') {
          // 文字列から数値のみを抽出
          const numStr = String(price).replace(/[^0-9]/g, '') || '0';
          soldPrice = parseInt(numStr, 10) || 0;
        }
      }

      const prizeStart = h.total_prize_start || 0;
      const prizeLatest = h.total_prize_latest || 0;

      // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
      const earnedPrize = prizeLatest - prizeStart;

      // RIO = 落札後に稼いだ賞金総額 / 落札価格
      const rio = soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;

      return sum + (isFinite(rio) ? rio : 0);
    }, 0) / horses.length
  ) : 0;

  // 集計ヘルパー
  const avg = (arr: number[]) => arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : 0;
  const median = (arr: number[]) => {
    if (!arr.length) return 0;
    const s = [...arr].sort((a, b) => a - b);
    const m = Math.floor(s.length / 2);
    return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
  };

  // フィルタ済みデータに基づく基本配列
  const prizes = filteredHorsesList
    .map(h => (typeof (h as any).total_prize_start === 'number' ? (h as any).total_prize_start : 0))
    .filter((n): n is number => typeof n === 'number');
  const weights = filteredHorsesList
    .map(h => (h.weight == null ? NaN : (typeof h.weight === 'number' ? h.weight : parseFloat(String(h.weight)))))
    .filter((n): n is number => !Number.isNaN(n));
  const ages = filteredHorsesList
    .map(h => (typeof h.age === 'number' ? h.age : (h.age ? parseFloat(String(h.age)) : NaN)))
    .filter((n): n is number => !Number.isNaN(n));
  const rois = filteredHorsesList
    .map(calcROIValue)
    .filter((n): n is number => isFinite(n));
  const diseaseYesCount = filteredHorsesList.filter(h => hasDisease((h as any).disease_tags)).length;
  const diseaseRatio = filteredHorsesList.length ? (diseaseYesCount / filteredHorsesList.length) * 100 : 0;

  // 性別グループ
  const sexGroups: Record<string, HorseWithCalculations[]> = {
    '牡': filteredHorsesList.filter(h => String(h.sex || '').includes('牡')),
    '牝': filteredHorsesList.filter(h => String(h.sex || '').includes('牝')),
    'セ': filteredHorsesList.filter(h => String(h.sex || '').includes('セ')),
  };

  // 平均価格を計算してメタデータを更新
  if (metadata) {
    const validPrices = horses
      .map(h => {
        // 価格が数値でない場合は0として扱う
        const price = h.sold_price;

        // null, undefined, 空文字の場合はスキップ
        if (price === null || price === undefined) {
          return null;
        }

        // 数値の場合はそのまま返す
        if (typeof price === 'number') {
          return price > 0 ? price : null;
        }

        // 文字列の場合は数値に変換を試みる
        const strPrice = String(price).trim();
        if (!strPrice) return null;

        const num = parseInt(strPrice.replace(/[^0-9]/g, ''), 10);
        return isNaN(num) || num <= 0 ? null : num;
      })
      .filter((price): price is number =>
        price !== null && price > 0
      );

    if (validPrices.length > 0) {
      const sum = validPrices.reduce((a, b) => a + b, 0);
      const avg = Math.round(sum / validPrices.length);
      metadata.average_price = avg;
    } else {
      metadata.average_price = 0;
      // デバッグ用: 馬のデータをログに出力（より詳細に）
      console.group('馬のデータの詳細');
      horses.forEach((h, index) => {
        console.group(`馬 ${index + 1}: ${h.name} (ID: ${h.id})`);
        console.log('sold_price:', h.sold_price, 'type:', typeof h.sold_price);
        console.log('unsold:', h.unsold);
        console.log('sold_price が数値かどうか:', typeof h.sold_price === 'number');
        console.log('sold_price が0より大きいか:', h.sold_price != null && h.sold_price > 0);
        console.log('sold_price が有効な数値か:', h.sold_price != null && !isNaN(Number(h.sold_price)));
        console.log('--- 生データ ---');
        console.log(JSON.stringify(h, null, 2));
        console.groupEnd();
      });
      console.groupEnd();

      console.warn('有効な落札価格データがありません。以下の可能性があります：', {
        '馬の総数': horses.length,
        'sold_price が数値の馬の数': horses.filter(h => typeof h.sold_price === 'number').length,
        'sold_price が0より大きい馬の数': horses.filter(h => h.sold_price != null && h.sold_price > 0).length,
        'unsold が true の馬の数': horses.filter(h => h.unsold).length,
        'sold_price が null または undefined の馬の数': horses.filter(h => h.sold_price === null || h.sold_price === undefined).length
      });
    }
  }

  // 旧: 指標ボタン用データ（不要のため削除）

  // 表示切替
  let tableHorses: HorseWithCalculations[] = [...filteredHorsesList];

  // 年齢を表示するヘルパー関数（null/undefined/空文字の場合は'-'を表示）
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return `${age}歳`;
  };

  // 落札価格を表示するヘルパー関数
  const displayPrice = formatPrice;

  // 賞金を表示するヘルパー関数
  const displayPrize = (value: number | string | null | undefined): string => {
    return formatPrize(value);
  };

  // ROIを計算するヘルパー関数
  const calcROI = (prizeLatest: number | null | undefined, prizeStart: number | null | undefined, price: number | string | null | undefined): string => {
    // 賞金データがない場合は計算不可
    if (prizeLatest === undefined || prizeLatest === null || prizeStart === undefined || prizeStart === null) return '-';

    // 価格を数値に変換
    const numPrice = price === null || price === undefined ? 0 : (typeof price === 'string' ? parseFloat(price) : price);

    // 価格が無効な場合は計算不可
    if (isNaN(numPrice) || numPrice <= 0) return '-';

    // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
    const earnedPrize = prizeLatest - prizeStart;

    // 落札価格が0以下の場合は計算不可
    if (numPrice <= 0) return '-';

    // RIO = 落札後に稼いだ賞金総額 / 落札価格
    const rio = (earnedPrize * 10000) / numPrice;

    // パーセンテージで返す（例: 0.15 → 15.0%）
    return (rio * 100).toFixed(1) + '%';
  };

  // ソート関数の型定義
  type SortFunction = (a: HorseWithCalculations, b: HorseWithCalculations) => number;
  const sortFunctions: Record<string, SortFunction> = {
    name: (a, b) => (a?.name ?? '').localeCompare(b?.name ?? '', 'ja'),
    sex: (a, b) => (a?.sex ?? '').localeCompare(b?.sex ?? '', 'ja'),
    weight: (a, b) => {
      const getNumericWeight = (weight: any): number => {
        if (weight === null || weight === undefined) return 0;
        if (typeof weight === 'number') return weight;
        const parsed = parseFloat(weight);
        return isNaN(parsed) ? 0 : parsed;
      };
      return getNumericWeight(a?.weight) - getNumericWeight(b?.weight);
    },
    age: (a, b) => {
      const ageA = typeof a?.age === 'number' ? a.age :
        (a?.age ? parseFloat(String(a.age)) : 0);
      const ageB = typeof b?.age === 'number' ? b.age :
        (b?.age ? parseFloat(String(b.age)) : 0);
      return ageA - ageB;
    },
    sire: (a, b) => (a?.sire ?? '').localeCompare(b?.sire ?? '', 'ja'),
    sold_price: (a, b) => {
      const aPrice = a?.sold_price !== null && a?.sold_price !== undefined ?
        (typeof a.sold_price === 'number' ? a.sold_price : 0) : 0;
      const bPrice = b.sold_price !== null && b.sold_price !== undefined ?
        (typeof b.sold_price === 'number' ? b.sold_price : 0) : 0;
      return aPrice - bPrice;
    },
    total_prize_start: (a, b) => (a.total_prize_start || 0) - (b.total_prize_start || 0),
    total_prize_latest: (a, b) => (a.total_prize_latest || 0) - (b.total_prize_latest || 0),
    roi: (a, b) => {
      const aSoldPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bSoldPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;

      // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
      const aEarnedPrize = (a.total_prize_latest || 0) - (a.total_prize_start || 0);
      const bEarnedPrize = (b.total_prize_latest || 0) - (b.total_prize_start || 0);

      // RIO = 落札後に稼いだ賞金総額 / 落札価格
      const aROI = aSoldPrice > 0 ? aEarnedPrize / aSoldPrice : 0;
      const bROI = bSoldPrice > 0 ? bEarnedPrize / bSoldPrice : 0;

      return aROI - bROI;
    },
    disease_tags: (a, b) => {
      // 病歴の有無を判定する関数
      const hasDisease = (horse: HorseWithCalculations) => {
        const tags = (horse as any).disease_tags;
        if (tags === undefined || tags === null || tags === '') return false;
        if (Array.isArray(tags)) {
          if (tags.length === 0) return false;
          return !tags.every(tag => {
            const strTag = String(tag).trim();
            return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
          });
        }
        const strTag = String(tags).trim();
        return !(strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。');
      };

      const aHasDisease = hasDisease(a) ? 1 : 0;
      const bHasDisease = hasDisease(b) ? 1 : 0;

      return aHasDisease - bHasDisease;
    },
  };

  if (sortKey && sortFunctions[sortKey]) {
    tableHorses = [...tableHorses].sort((a, b) => {
      const res = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? res : -res;
    });
  }

  // ソートハンドラー
  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  // 行クリックハンドラー
  const handleRowClick = (id: string | number) => {
    router.push(`/horses/${id}`);
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-3">
          <FiltersPanel
            filters={filters}
            onChange={(next) => setFilters(prev => ({ ...prev, ...next }))}
            onReset={() => setFilters({ ...DEFAULT_FILTERS })}
            sireSuggestions={sireSuggestions}
            onExportAll={handleExportAll}
            onExportFiltered={handleExportFiltered}
          />
        </div>

        <div className="flex items-center justify-between mb-3 gap-3">
          <div className="text-sm text-gray-600">
            一覧: {total}頭中 {(page - 1) * limit + 1} - {Math.min(page * limit, total)} 件を表示
          </div>
          <div className="flex items-center gap-2">
            {/* クイック検索（IDまたは名前/血統） */}
            <input
              type="text"
              className="border rounded px-2 py-1 h-8 text-xs w-[220px]"
              placeholder="ID または 馬名/父/母/母父 で検索"
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  setPage(1);
                  setSearch(searchInput);
                }
              }}
            />
            <Button
              variant="outline"
              onClick={() => {
                setPage(1);
                setSearch(searchInput);
              }}
              disabled={loading}
            >検索</Button>
            <Button
              variant="outline"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page <= 1 || loading}
            >前へ</Button>
            <Button
              variant="outline"
              onClick={() => setPage(p => (p * limit < total ? p + 1 : p))}
              disabled={page * limit >= total || loading}
            >次へ</Button>
          </div>
        </div>

        <div className="grid [grid-template-columns:minmax(0,1fr)_240px] gap-6 items-start">
          <div className="min-w-0">
            {/* 旧: 表示切替ボタン（削除） */}
            <HorseTable
              horses={filteredHorsesList}
              onRowClick={handleRowClick}
            />
          </div>
          <aside className="col-start-2 w-[240px]">
            <div className="sticky top-4 space-y-4">
              <div className="bg-white rounded-md border p-4 text-sm">
                <div className="text-gray-500 mb-2">絞り込み結果の統計</div>
                <div className="space-y-3">
                  <div>
                    <div className="text-xs text-gray-500">頭数</div>
                    <div className="text-base font-semibold">{filteredHorsesList.length}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">病歴</div>
                    <div className="text-sm">{diseaseRatio.toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">獲得賞金</div>
                    <div className="text-xs">平均 {Math.round(avg(prizes)).toLocaleString()} 円</div>
                    <div className="text-xs">中央値 {Math.round(median(prizes)).toLocaleString()} 円</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">馬体重</div>
                    <div className="text-xs">平均 {avg(weights).toFixed(1)} kg</div>
                    <div className="text-xs">中央値 {median(weights).toFixed(1)} kg</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">年齢</div>
                    <div className="text-xs">平均 {avg(ages).toFixed(2)} 歳</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">ROI</div>
                    <div className="text-xs">平均 {avg(rois).toFixed(1)}</div>
                    <div className="text-xs">中央値 {median(rois).toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500">性別別（賞金）</div>
                    <div className="space-y-2 mt-1">
                      {(['牡', '牝', 'セ'] as const).map(sex => {
                        const group = sexGroups[sex] || [];
                        const gPrizes = group.map((h: HorseWithCalculations) => (h as any).total_prize_start || 0);
                        return (
                          <div key={sex} className="text-xs">
                            <div className="font-medium">{sex}</div>
                            <div>平 {Math.round(avg(gPrizes)).toLocaleString()}</div>
                            <div>中 {Math.round(median(gPrizes)).toLocaleString()}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>

              {!isFiltered && (
                <div className="bg-white rounded-md border p-4 text-sm">
                  <details open={false}>
                    <summary className="cursor-pointer select-none text-gray-600">全体データ（折りたたみ）</summary>
                    <div className="mt-3 space-y-2 text-xs">
                      <div>総馬数: {horses.length}</div>
                      <div>平均落札価格: {formatCurrency(metadata.average_price)}</div>
                      <div>平均ROI: {avgRIO.toFixed(2)}%</div>
                    </div>
                  </details>
                </div>
              )}
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
