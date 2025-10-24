'use client';

import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useState, useEffect, useMemo } from 'react';
import { DiseaseTags, extractDiseaseTags } from './diseaseTags';
import SexBadge from '../components/SexBadge';
import { getAuctionHistories } from '../api/horsesApi';
import DateInfoCard from './components/DateInfoCard';
import { format, parseISO, formatDistanceToNow, isDate } from 'date-fns';

// 日付をフォーマットする関数
function formatDate(date: string | string[] | Date | null | undefined, formatStr: string = 'yyyy/MM/dd'): string {
  if (!date) return '';
  
  try {
    // 配列の場合は最初の要素を使用
    const dateStr = Array.isArray(date) ? date[0] : date;
    
    // すでに Date オブジェクトの場合はそのまま使用
    const dateObj = isDate(dateStr) ? dateStr : new Date(dateStr);
    
    // 無効な日付の場合は空文字を返す
    if (isNaN(dateObj.getTime())) return '';
    
    return format(dateObj, formatStr);
  } catch (e) {
    console.error('日付のフォーマットに失敗しました:', e);
    return '';
  }
}

import { ja } from 'date-fns/locale';
import { 
  formatWeight, 
  formatPrizeFromYen, 
  calculateGrowthRate, 
  toArray, 
  formatDate as formatDateUtil,
  formatPrizeMan,
  formatCurrency
} from '../../../src/utils/format';
import { BaseAuctionHistory } from '../../../src/types/horse';

// AuctionHistory 型を拡張して必要なプロパティを追加
type AuctionHistory = Omit<BaseAuctionHistory, 'auction_date'> & {
  id?: string | number;
  horse_id?: string | number;
  auction_date: string | string[];  // undefined を許容しない
  sold_price?: number | null;
  total_prize_start?: number;
  total_prize_latest?: number;
  weight?: number | null;
  seller?: string | null;
  is_unsold?: boolean;
  unsold?: boolean;
  comment?: string;
  created_at?: string;
  updated_at?: string;
  detail_url?: string | null;
  auction_url?: string;
  price?: number;
  name?: string;
  sex?: string;
  age?: string | number;
  race_record?: any;
  primary_image?: string;
  disease_tags?: string;
  [key: string]: any; // その他のプロパティに対応
};
import { HorseWithCalculations } from '../../../src/types/horse';
import { ExtendedAuctionHistory, RaceRecord } from './types';
import { HeaderCard } from './components';
import ExternalLinks from './components/ExternalLinks';
import { ErrorMessage, SimpleError } from './components/ErrorDisplay';
import dynamic from 'next/dynamic';
const LoadingSpinner = dynamic(() => import('./components/LoadingSpinner'), { ssr: false });
import { HorseHeader } from './components/HorseHeader';
import AuctionHistoryCard from './components/AuctionHistoryCard';
import { CommentCard } from './components/CommentCard';
import PrizeCard from './components/PrizeCard';
import {
  Button,
  Typography,
  Card,
  CardContent,
  CardHeader,
  Tabs,
  Tab,
  Box,
  Badge,
} from '@mui/material';
import HorseImage from '../../../src/components/HorseImage';
import { normalizeImageUrl } from '../../../src/utils/url';
import { getHorseData as getHorseDataFromApi } from '../../../src/utils/horseApi';

// 型定義は ./types.ts に移動しました

// HorseWithCalculations を拡張して、ページ固有のプロパティを追加
interface HorseWithPageProps extends Omit<HorseWithCalculations, 'history' | 'auction_histories' | 'effectiveAuction' | 'auction_history'> {
  // 基本情報
  id: string | number;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  weight?: number | null;
  
  // オークション情報
  auction_id?: string;
  history: AuctionHistory[];  // オークション履歴
  auction_history?: AuctionHistory[];  // オークション履歴（互換性のため）
  sold_price?: number | null;  // 落札価格
  total_prize_start: number;   // 初出走前の獲得賞金
  total_prize_latest: number | null;  // 最新の獲得賞金
  is_unsold?: boolean;  // 未落札フラグ
  unsold?: boolean;     // 未落札フラグ（互換性のため）
  unsold_count: number; // 未落札回数
  seller?: string | null;      // 出品者
  
  // 画像関連
  image_url: string | { image_url: string };  // 互換性のため
  primary_image: string;  // メイン画像URL
  
  // リンク
  jbis_url?: string;  // JRA-VAN URL
  detail_url: string; // 詳細ページURL
  rakuten_url?: string; // 楽天競馬URL
  auction_url?: string; // オークションURL（互換性のため）
  
  // その他
  disease_tags: string[];  // 疾病タグ
  created_at?: string;     // 作成日時
  updated_at?: string;     // 更新日時
  dam_sire?: string;       // 母の父（互換性のため）
  comment?: string;        // コメント
  
  // 表示用フォーマット済みデータ
  display_price: string;   // 表示用価格
  display_weight: string;  // 表示用体重
  display_prize: string;   // 表示用賞金
  display_roi: string;     // 表示用ROI
  
  // ソート用データ
  sort_price: number;      // 価格ソート用
  sort_prize: number;      // 賞金ソート用
  sort_roi: number;        // ROIソート用
  
  // 計算済みデータ
  roi: number;             // 投資収益率
  price_per_kg: number;    // キロ単価
};
interface HorseData {
  metadata: any;
  horses: HorseWithPageProps[];
}

interface CommentedHistory extends ExtendedAuctionHistory {
  originalIndex: number;
}

interface HorseDetailContentProps {
  horse: HorseWithPageProps;
  hasComments: boolean;
  latestHistory: ExtendedAuctionHistory | null;
}

interface PageProps {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

// seller を配列/JSON配列文字列/二重エンコードからプレーン日本語に整形
function normalizeSeller(value: any): string {
  try {
    if (Array.isArray(value)) {
      return value.length > 0 ? String(value[0] ?? '') : '';
    }
    if (typeof value === 'string') {
      let str: any = value.trim();
      for (let i = 0; i < 2; i++) {
        const looksJson = str.startsWith('[') || str.startsWith('{') || str.startsWith('"');
        if (!looksJson) break;
        try {
          const parsed = JSON.parse(str);
          if (Array.isArray(parsed)) {
            return parsed.length > 0 ? String(parsed[0] ?? '') : '';
          }
          if (typeof parsed === 'string') {
            str = parsed.trim();
            continue;
          }
          break;
        } catch {
          break;
        }
      }
      return str;
    }
  } catch {
    return typeof value === 'string' ? value : '';
  }
  return '';
}

// 価格表示は utils/price の仕様化ロジックを使用（UIは変えない）

/**
 * 馬データを取得する関数
 * @param horseId 取得する馬のID
 * @returns 馬データとエラー情報を含むオブジェクト
 */
async function getHorseData(horseId: string): Promise<{ horse: HorseWithPageProps | null; error: string | null }> {
  if (!horseId || typeof horseId !== 'string') {
    return { horse: null, error: '無効な馬IDです' };
  }

  try {
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const url = `${apiBase}/api/horses/${encodeURIComponent(horseId)}?_=${Date.now()}`;
    console.log('API Request URL:', url);  // デバッグ用
    console.log('[horse detail] Fetch:', url);

    const response = await fetch(url, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      cache: 'no-store',
      credentials: 'same-origin'
    });
    
    // レスポンスの生データを取得
    const responseData = await response.clone().json();
    console.log('API Response Data:', JSON.stringify(responseData, null, 2));
    
    // デバッグ用: レスポンスに含まれるプロパティをログ出力
    if (responseData) {
      console.log('Response data properties:', Object.keys(responseData));
      if (responseData.horse) {
        console.log('Horse data properties:', Object.keys(responseData.horse));
        console.log('Horse URLs - jbis:', responseData.horse.jbis_url, 
                   'detail:', responseData.horse.detail_url, 
                   'rakuten:', responseData.horse.rakuten_url);
      }
    }
    if (!response.ok) {
      // 404 の場合は一覧からフォールバック検索
      if (response.status === 404) {
        console.warn('[horse detail] Not found by ID, trying fallback via /api/horses');
        const apiBaseList = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        // limit を大きくして取りこぼしを防ぐ
        const listUrl = `${apiBaseList}/api/horses?limit=10000&_=${Date.now()}`;
        console.log('Fallback API Request URL:', listUrl);  // デバッグ用
        const listRes = await fetch(listUrl, { headers: { 'Accept': 'application/json' }, cache: 'no-store' });
        if (listRes.ok) {
          const listJson = await listRes.json();
          const horses: any[] = Array.isArray(listJson?.horses) ? listJson.horses : [];
          // まず id/auction_id で検索
          const numId = Number(horseId);
          let candidate = horses.find(h => (
            (h.id === horseId) ||
            (typeof h.id === 'number' && !isNaN(numId) && h.id === numId) ||
            (h.auction_id && (String(h.auction_id) === String(horseId)))
          ));

          // 見つからない場合、静的データから名前等を取得して名前で突き合わせ
          if (!candidate) {
            try {
              const staticRes = await fetch('/data/horses.json', { cache: 'no-store' });
              if (staticRes.ok) {
                const staticHorses = await staticRes.json();
                const staticBase = Array.isArray(staticHorses)
                  ? staticHorses.find((h: any) => String(h.id) === String(horseId) || String(h.auction_id) === String(horseId))
                  : null;
                const baseName = staticBase?.name?.trim();
                const baseAge = staticBase?.age;
                if (baseName) {
                  const normalize = (s: any) => String(s || '')
                    .toLowerCase()
                    .replace(/[\s\u3000]/g, ''); // 半角/全角スペース除去
                  // 名前一致、かつ可能なら年齢も一致を優先
                  candidate = horses.find(h => (
                    normalize(h.name) === normalize(baseName) &&
                    (baseAge === undefined || baseAge === null || Number(h.age) === Number(baseAge))
                  ));
                  // それでもなければ、部分一致を試す
                  if (!candidate) {
                    candidate = horses.find(h => normalize(h.name) === normalize(baseName));
                  }
                }
              }
            } catch (e) {
              console.warn('[horse detail] static horses.json lookup failed:', e);
            }
          }

          if (!candidate) {
            // さらに見つからない場合、静的データ(staticBase)があればそれで詳細を構築して返す
            try {
              const staticRes = await fetch('/data/horses.json', { cache: 'no-store' });
              if (staticRes.ok) {
                const staticHorses = await staticRes.json();
                const staticBase = Array.isArray(staticHorses)
                  ? staticHorses.find((h: any) => String(h.id) === String(horseId) || String(h.auction_id) === String(horseId))
                  : null;
                if (staticBase) {
                  const historyEntry: ExtendedAuctionHistory = {
                    id: staticBase.id || `temp-${Date.now()}`,
                    horse_id: staticBase.horse_id || staticBase.id || `temp-horse-${Date.now()}`,
                    auction_date: staticBase.auction_date || new Date().toISOString().split('T')[0],
                    name: staticBase.name || '不明',
                    sex: staticBase.sex || '不明',
                    age: Number(staticBase.age) || 0,
                    seller: staticBase.seller || '不明',
                    race_record: staticBase.race_record || '未出走',
                    comment: staticBase.comment || '',
                    sold_price: staticBase.sold_price ?? null,
                    total_prize_start: staticBase.total_prize_start ?? 0,
                    total_prize_latest: staticBase.total_prize_latest ?? 0,
                    is_unsold: staticBase.is_unsold ?? false,
                    created_at: staticBase.created_at || new Date().toISOString(),
                    unsold: (staticBase.unsold ?? false) || (staticBase.is_unsold ?? false),
                    detail_url: staticBase.auction_url || '',
                    primary_image: staticBase.primary_image || staticBase.image_url || '',
                    disease_tags: Array.isArray(staticBase.disease_tags) ? staticBase.disease_tags.join(',') : (staticBase.disease_tags || ''),
                    weight: staticBase.weight
                  };

                  const horse: HorseWithPageProps = {
                    // 基本情報 (BaseHorse から継承)
                    id: staticBase.id ?? horseId,
                    auction_id: staticBase.auction_id,
                    sex: staticBase.sex || '不明',
                    sire: staticBase.sire || '不明',
                    dam: staticBase.dam || '不明',
                    damsire: staticBase.dam_sire || staticBase.damsire || '不明',
                    image_url: staticBase.primary_image || staticBase.image_url || '',
                    jbis_url: staticBase.jbis_url,
                    detail_url: staticBase.detail_url || staticBase.auction_url || '',
                    
                    // Horse インターフェースのプロパティ
                    disease_tags: Array.isArray(staticBase.disease_tags) 
                      ? staticBase.disease_tags 
                      : (staticBase.disease_tags || '').split(',').filter(Boolean),
                    created_at: staticBase.created_at || new Date().toISOString(),
                    updated_at: staticBase.updated_at || new Date().toISOString(),
                    sold_price: staticBase.sold_price ?? null,
                    is_unsold: staticBase.is_unsold ?? false,
                    seller: staticBase.seller || '不明',
                    total_prize_latest: typeof staticBase.total_prize_latest === 'string' 
                      ? parseFloat(staticBase.total_prize_latest) 
                      : (staticBase.total_prize_latest ?? 0),
                    auction_url: staticBase.auction_url,
                    unsold: (staticBase.unsold ?? false) || (staticBase.is_unsold ?? false),
                    primary_image: staticBase.primary_image || staticBase.image_url || '',
                    rakuten_url: staticBase.rakuten_url,
                    unsold_count: typeof staticBase.unsold_count === 'string' 
                      ? parseInt(staticBase.unsold_count, 10) 
                      : (staticBase.unsold_count || 0),
                    weight: typeof staticBase.weight === 'string' 
                      ? parseFloat(staticBase.weight) 
                      : (staticBase.weight || null),
                    
                    // HorseWithCalculations のプロパティ
                    total_prize_start: staticBase.total_prize_start ?? 0,
                    roi: 0,
                    price_per_kg: 0,
                    display_price: formatPrizeFromYen(staticBase.sold_price || 0),
                    display_weight: formatWeight(staticBase.weight),
                    display_prize: formatPrizeFromYen(staticBase.total_prize_latest ?? 0),
                    display_roi: '0%',
                    sort_price: Number(staticBase.sold_price) || 0,
                    sort_prize: staticBase.total_prize_latest ?? 0,
                    sort_roi: 0,
                    
                    // その他のプロパティ
                    name: staticBase.name || '不明',
                    age: Number(staticBase.age) || 0,
                    history: [historyEntry],
                    auction_history: [historyEntry]
                  };

                  console.log('[horse detail] Use static horses.json mapped horse:', horse);
                  return { horse, error: null };
                }
              }
            } catch (e) {
              console.warn('[horse detail] static-only mapping failed:', e);
            }

            const text = await response.text();
            console.error('[horse detail] API Error (no fallback match):', response.status, text);
            throw new Error('馬データの取得に失敗しました');
          }

          // 一覧の1件分から詳細用オブジェクトを構築
          const horseBaseData = candidate;
          const historyEntry: ExtendedAuctionHistory = {
            id: horseBaseData.id || `temp-${Date.now()}`,
            horse_id: horseBaseData.horse_id || horseBaseData.id || `temp-horse-${Date.now()}`,
            auction_date: horseBaseData.auction_date || new Date().toISOString().split('T')[0],
            sold_price: horseBaseData.sold_price ?? null,
            total_prize_start: horseBaseData.total_prize_start ?? 0,
            total_prize_latest: horseBaseData.total_prize_latest ?? 0,
            weight: horseBaseData.weight,
            seller: horseBaseData.seller || '不明',
            is_unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false) || (horseBaseData.unsold_count > 0),
            comment: horseBaseData.comment || '',
            created_at: horseBaseData.created_at || new Date().toISOString(),
            // Extended properties
            name: horseBaseData.name || '不明',
            sex: horseBaseData.sex || '不明',
            age: Number(horseBaseData.age) || 0,
            race_record: horseBaseData.race_record || '未出走',
            detail_url: horseBaseData.detail_url || horseBaseData.auction_url || '',
            primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
            disease_tags: Array.isArray(horseBaseData.disease_tags) 
              ? horseBaseData.disease_tags.join(',') 
              : (horseBaseData.disease_tags || '')
          };

          // HorseWithPageProps に合わせてオブジェクトを構築
          const horse: HorseWithPageProps = {
            // BaseHorse プロパティ
            id: horseBaseData.id ?? horseId,
            auction_id: horseBaseData.auction_id,
            sex: horseBaseData.sex || '不明',
            sire: horseBaseData.sire || '不明',
            dam: horseBaseData.dam || '不明',
            damsire: horseBaseData.dam_sire || horseBaseData.damsire || '不明',
            image_url: horseBaseData.primary_image || horseBaseData.image_url || '',
            jbis_url: horseBaseData.jbis_url,
            detail_url: horseBaseData.detail_url || horseBaseData.auction_url || '',
            
            // Horse インターフェースのプロパティ
            disease_tags: Array.isArray(horseBaseData.disease_tags) 
              ? horseBaseData.disease_tags 
              : (horseBaseData.disease_tags || '').split(',').filter(Boolean),
            created_at: horseBaseData.created_at || new Date().toISOString(),
            updated_at: horseBaseData.updated_at || new Date().toISOString(),
            sold_price: horseBaseData.sold_price ?? null,
            is_unsold: horseBaseData.is_unsold ?? false,
            seller: horseBaseData.seller || '不明',
            total_prize_latest: typeof horseBaseData.total_prize_latest === 'string' 
              ? parseFloat(horseBaseData.total_prize_latest) 
              : (horseBaseData.total_prize_latest ?? 0),
            auction_url: horseBaseData.auction_url,
            primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
            rakuten_url: horseBaseData.rakuten_url,
            unsold_count: typeof horseBaseData.unsold_count === 'string' 
              ? parseInt(horseBaseData.unsold_count, 10) 
              : (horseBaseData.unsold_count || 0),
            weight: typeof horseBaseData.weight === 'string' 
              ? parseFloat(horseBaseData.weight) 
              : (horseBaseData.weight || null),
            
            // HorseWithCalculations のプロパティ
            total_prize_start: horseBaseData.total_prize_start ?? 0,
            roi: 0,
            price_per_kg: 0,
            display_price: formatPrizeFromYen(horseBaseData.sold_price || 0),
            display_weight: formatWeight(horseBaseData.weight),
            display_prize: formatPrizeFromYen(horseBaseData.total_prize_latest ?? 0),
            display_roi: '0%',
            sort_price: Number(horseBaseData.sold_price) || 0,
            sort_prize: horseBaseData.total_prize_latest ?? 0,
            sort_roi: 0,
            
            // その他のプロパティ
            name: horseBaseData.name || '不明',
            age: Number(horseBaseData.age) || 0,
            history: [{
              // 基本プロパティ
              ...historyEntry,
              // 必須プロパティのデフォルト値を設定
              id: historyEntry.id || `temp-${Date.now()}`,
              horse_id: historyEntry.horse_id || `horse-${Date.now()}`,
              auction_date: historyEntry.auction_date || new Date().toISOString().split('T')[0],
              sold_price: historyEntry.sold_price ?? null,
              total_prize_start: historyEntry.total_prize_start ?? 0,
              total_prize_latest: historyEntry.total_prize_latest ?? 0,
              weight: historyEntry.weight ?? null,
              seller: historyEntry.seller || '不明',
              is_unsold: historyEntry.is_unsold ?? false,
              comment: historyEntry.comment || '',
              created_at: historyEntry.created_at || new Date().toISOString(),
              // ExtendedAuctionHistory 固有のプロパティ
              name: historyEntry.name || horseBaseData.name || '不明',
              sex: historyEntry.sex || horseBaseData.sex || '不明',
              age: historyEntry.age || horseBaseData.age || 0
            }],
            // 未落札回数が0より大きい場合にのみunsoldをtrueに設定
            unsold: (horseBaseData.unsold_count > 0) || (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false)
          };

          console.log('[horse detail] Fallback mapped horse:', horse);
          return { horse, error: null };
        }

      }
      const text = await response.text();
      console.error('[horse detail] API Error:', response.status, text);
      throw new Error('馬データの取得に失敗しました');
    }

    const data = await response.json();
    console.log('[horse detail] Raw API response:', JSON.stringify(data, null, 2));
    
    // バックエンドの単体取得は HorseWithPageProps に変換されたデータを返す想定。
    // 既存UIが必要とするフィールドに合わせてマッピング。
    const horseBaseData = data || {};
    
    // デバッグ用に元のデータをログ出力
    console.log('Debug - horseBaseData URLs:', {
      detail_url: horseBaseData.detail_url,
      rakuten_url: horseBaseData.rakuten_url,
      auction_url: horseBaseData.auction_url,
      allKeys: Object.keys(horseBaseData)
    });
    
    // APIから受け取った値をそのまま使用
    const detailUrl = horseBaseData.detail_url || '';
    const rakutenUrl = horseBaseData.rakuten_url || '';
    const auctionUrl = horseBaseData.auction_url || '';
    
    // デバッグ用にURLの値をログ出力
    console.log('Debug - Raw URLs from API:', {
      detail_url: detailUrl,
      rakuten_url: rakutenUrl,
      auction_url: auctionUrl,
      jbis_url: horseBaseData.jbis_url
    });

    const historyEntry: ExtendedAuctionHistory = {
      id: horseBaseData.id || `temp-${Date.now()}`,
      horse_id: horseBaseData.horse_id || horseBaseData.id || `temp-horse-${Date.now()}`,
      auction_date: horseBaseData.auction_date || new Date().toISOString().split('T')[0],
      name: horseBaseData.name || '不明',
      sex: horseBaseData.sex || '不明',
      age: Number(horseBaseData.age) || 0,
      seller: horseBaseData.seller || '不明',
      race_record: horseBaseData.race_record || '未出走',
      comment: horseBaseData.comment || '',
      sold_price: horseBaseData.sold_price ?? null,
      total_prize_start: horseBaseData.total_prize_start ?? 0,
      total_prize_latest: horseBaseData.total_prize_latest ?? 0,
      weight: horseBaseData.weight ?? null,
      is_unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false) || (horseBaseData.unsold_count > 0),
      created_at: horseBaseData.created_at || new Date().toISOString(),
      detail_url: detailUrl,
      primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
      disease_tags: Array.isArray(horseBaseData.disease_tags) 
        ? horseBaseData.disease_tags 
        : (horseBaseData.disease_tags || '').split(',').filter(Boolean),
      // 非推奨プロパティ（互換性のため）
      unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsound ?? false) || (horseBaseData.unsold_count > 0)
    };

    // デバッグ用にAPIレスポンスをログ出力
    console.log('Debug - API Response data:', {
      horseBaseData,
      auction_id: horseBaseData.auction_id,
      hasAuctionId: !!horseBaseData.auction_id,
      data: data
    });

    // デバッグ用にデータをログ出力
    console.log('Debug - horseBaseData:', horseBaseData);
    console.log('Debug - data:', data);

    // APIから受け取ったJBIS URLをそのまま使用
    const jbisUrl = horseBaseData.jbis_url || '';

    const horse: HorseWithPageProps = {
      // 基本情報
      id: horseBaseData.id ?? horseId,
      name: horseBaseData.name || '不明',
      sex: horseBaseData.sex || '不明',
      age: Number(horseBaseData.age) || 0, // 数値に変換
      sire: horseBaseData.sire || '不明',
      dam: horseBaseData.dam || '不明',
      damsire: horseBaseData.dam_sire || horseBaseData.damsire || '不明',
      weight: typeof horseBaseData.weight === 'string' ? parseFloat(horseBaseData.weight) : horseBaseData.weight || null,
      
      // オークション情報
      auction_id: data?.auction_id || horseBaseData.auction_id, // APIレスポンスのルートからauction_idを取得
      history: [historyEntry],
      sold_price: horseBaseData.sold_price ?? null,
      total_prize_start: horseBaseData.total_prize_start ?? 0,
      total_prize_latest: typeof horseBaseData.total_prize_latest === 'string' 
        ? parseFloat(horseBaseData.total_prize_latest) 
        : (horseBaseData.total_prize_latest ?? 0),
      is_unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false),
      unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false),
      unsold_count: typeof horseBaseData.unsold_count === 'string' 
        ? parseInt(horseBaseData.unsold_count, 10) 
        : (horseBaseData.unsold_count || 0),
      seller: horseBaseData.seller || '不明',
      
      // 画像関連
      image_url: horseBaseData.primary_image || horseBaseData.image_url || '',
      primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
      
      // URL関連
      jbis_url: jbisUrl,
      detail_url: detailUrl,
      rakuten_url: rakutenUrl,
      auction_url: auctionUrl,
      
      // その他
      disease_tags: Array.isArray(horseBaseData.disease_tags) 
        ? horseBaseData.disease_tags 
        : (horseBaseData.disease_tags || '').split(',').filter(Boolean),
      created_at: horseBaseData.created_at || new Date().toISOString(),
      updated_at: horseBaseData.updated_at || new Date().toISOString(),
      
      // 表示用
      display_price: formatPrizeFromYen(horseBaseData.sold_price || 0),
      display_weight: formatWeight(horseBaseData.weight),
      display_prize: formatPrizeFromYen(horseBaseData.total_prize_latest ?? 0),
      display_roi: '0%',
      sort_price: Number(horseBaseData.sold_price) || 0,
      sort_prize: horseBaseData.total_prize_latest ?? 0,
      sort_roi: 0,
      
      // HorseWithCalculations から必要な追加プロパティ
      roi: 0,
      price_per_kg: 0
    };
    
    console.log('Debug - Mapped horse URLs:', {
      detail_url: horse.detail_url,
      rakuten_url: horse.rakuten_url,
      auction_url: horse.auction_url,
      jbis_url: horse.jbis_url
    });

    // HorseWithPageProps に変換するヘルパー関数
    const toHorseWithPageProps = (horse: HorseWithPageProps): HorseWithPageProps => ({
      ...horse,
      // 必須プロパティを上書き
      history: Array.isArray(horse.history) 
        ? horse.history.map(h => ({
            ...h,
            // ExtendedAuctionHistory に必要なプロパティを追加
            id: (h as any).id || `temp-${Date.now()}`,
            horse_id: (h as any).horse_id || horse.id || `temp-horse-${Date.now()}`,
            auction_date: h.auction_date || new Date().toISOString().split('T')[0],
            sold_price: h.sold_price ?? null,
            total_prize_start: (h as any).total_prize_start ?? 0,
            total_prize_latest: (h as any).total_prize_latest ?? 0,
            weight: h.weight ?? null,
            seller: (h as any).seller || '不明',
            is_unsold: (h as any).is_unsold || (h as any).unsold || false,
            comment: (h as any).comment || '',
            created_at: (h as any).created_at || new Date().toISOString(),
            // 拡張プロパティ
            name: (h as any).name || horse.name || '不明',
            sex: (h as any).sex || horse.sex || '不明',
            age: typeof (h as any).age === 'number' ? (h as any).age : (Number((h as any).age) || 0),
            race_record: (h as any).race_record || '未出走',
            detail_url: (h as any).detail_url || horse.detail_url || '',
            primary_image: (h as any).primary_image || horse.primary_image || '',
            disease_tags: Array.isArray((h as any).disease_tags) 
              ? (h as any).disease_tags 
              : (typeof (h as any).disease_tags === 'string' 
                  ? (h as any).disease_tags.split(',').filter(Boolean) 
                  : [])
          }))
        : [],
      // 必須プロパティを追加
      disease_tags: (() => {
        const tags = (horse as any).disease_tags || [];
        return Array.isArray(tags) 
          ? tags 
          : (typeof tags === 'string' 
              ? tags.split(',').filter(Boolean) 
              : []);
      })(),
      // 明示的に文字列に変換
      primary_image: (() => {
        const img = horse.primary_image || horse.image_url || '';
        // オブジェクトの場合は JSON 文字列化、それ以外は文字列に変換
        return img && typeof img === 'object' ? JSON.stringify(img) : String(img);
      })(),
      detail_url: horse.detail_url || '',
      // その他の必須プロパティ
      rakuten_url: (horse as any).rakuten_url || '',
      auction_url: (horse as any).auction_url || '',
      unsold_count: (horse as any).unsold_count || 0,
      dam_sire: (horse as any).dam_sire || horse.damsire || '不明'
    });

    const horseWithPageProps = toHorseWithPageProps(horse);

    console.log('Debug - Generated horse object:', horseWithPageProps);
    
    // デバッグ用にマッピング後のデータをログ出力
    console.log('Debug - Mapped horse data:', {
      jbis_url: horseWithPageProps.jbis_url,
      auction_id: horseWithPageProps.auction_id,
      hasAuctionId: !!horseWithPageProps.auction_id
    });

    console.log('[horse detail] Mapped horse:', JSON.stringify({
      ...horseWithPageProps,
      // 大きなデータは省略
      history: horseWithPageProps.history?.map(h => ({
        auction_date: h.auction_date,
        sold_price: h.sold_price,
        detail_url: h.detail_url,
        seller: h.seller
      }))
    }, null, 2));
    
    return { horse: horseWithPageProps, error: null };
  } catch (error) {
    console.error('馬データの取得中にエラーが発生しました:', error);
    return { 
      horse: null, 
      error: error instanceof Error ? error.message : '不明なエラーが発生しました' 
    };
  }
}


// ページのパラメータ型
interface PageProps {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

// レース成績表示用のコンポーネント
const RaceRecordDisplay = ({ record, raceRecords }: { record: any, raceRecords?: any }) => {
  try {
    // race_records が存在する場合は、それを優先的に使用
    if (raceRecords) {
      // race_records が文字列の場合はパースを試みる
      if (typeof raceRecords === 'string') {
        try {
          raceRecords = JSON.parse(raceRecords);
        } catch (e) {
          console.error('race_records のパースに失敗しました:', e);
        }
      }
      
      // パース後のオブジェクトを確認
      if (raceRecords && typeof raceRecords === 'object') {
        // formatted_record が存在する場合はそれを表示
        if (raceRecords.formatted_record) {
          return <span className="font-medium">{raceRecords.formatted_record}</span>;
        }
        // total_races と wins が存在する場合はフォーマットして表示
        else if (raceRecords.total_races !== undefined && raceRecords.wins !== undefined) {
          const wins = raceRecords.wins || 0;
          const seconds = raceRecords.seconds || 0;
          const thirds = raceRecords.thirds || 0;
          const others = Math.max(0, raceRecords.total_races - wins - seconds - thirds);
          return (
            <span className="font-medium">
              {`${raceRecords.total_races}戦${wins}勝[${wins}-${seconds}-${thirds}-${others}]`}
            </span>
          );
        }
      }
    }

    // 従来の record の処理（下位互換性のため保持）
    if (record) {
      // 文字列の場合
      if (typeof record === 'string') {
        // 空のオブジェクトを表す文字列の場合
        if (record === '{}' || record === '[]') {
          return <span className="font-medium">未出走</span>;
        }
        // JSON文字列の可能性がある場合
        if ((record.startsWith('{') && record.endsWith('}')) || 
            (record.startsWith('[') && record.endsWith(']'))) {
          try {
            const parsed = JSON.parse(record);
            return <RaceRecordDisplay record={parsed} />;
          } catch (e) {
            return <span className="font-medium">{record}</span>;
          }
        }
        return <span className="font-medium">{record}</span>;
      }
      
      // オブジェクトの場合
      if (typeof record === 'object') {
        // 空のオブジェクトの場合は「未出走」を表示
        if (Object.keys(record).length === 0) {
          return <span className="font-medium">未出走</span>;
        }
        // total_races と wins が存在する場合は新しい形式で表示
        if (record.total_races !== undefined && record.wins !== undefined) {
          const wins = record.wins || 0;
          const seconds = record.seconds || 0;
          const thirds = record.thirds || 0;
          const others = Math.max(0, record.total_races - wins - seconds - thirds);
          return (
            <span className="font-medium">
              {`${record.total_races}戦${wins}勝[${wins}-${seconds}-${thirds}-${others}]`}
            </span>
          );
        }
        // formatted_record が存在する場合
        else if (record.formatted_record) {
          // formatted_record が「11戦0勝」のような形式の場合、そのまま表示
          return <span className="font-medium">{record.formatted_record}</span>;
        }
      }
    }
    
    return <span className="font-medium">データなし</span>;
  } catch (e) {
    console.error('レース成績の表示中にエラーが発生しました:', e);
    return <span className="font-medium">データなし</span>;
  }
};

// ページコンポーネント (Client Component)
export default function HorseDetailPage({ params }: PageProps) {
  const router = useRouter();
  const [selectedTab, setSelectedTab] = useState<number>(0);
  const [horse, setHorse] = useState<HorseWithPageProps | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  
  // コメントと最新履歴の状態を管理
  const [pageState, setPageState] = useState<{
    hasComments: boolean;
    latestHistory: ExtendedAuctionHistory | null;
  }>({
    hasComments: false,
    latestHistory: null
  });
  
  // デバッグ用: マウント時のパラメータをログ出力
  // 注意: このコンポーネント内では pageState.hasComments と pageState.latestHistory を使用してください
  // 変数名の重複を避けるため、分割代入は行わないでください
  useEffect(() => {
    console.log('HorseDetailPage mounted with params:', params);
  }, [params]);
  
  // デバッグ用: 馬データが更新されたらログ出力
  useEffect(() => {
    if (horse) {
      console.log('Horse data updated:', {
        id: horse.id,
        name: horse.name,
        comment: horse.comment,
        disease_tags: horse.disease_tags,
        hasComments: pageState.hasComments,
        latestHistory: pageState.latestHistory ? {
          id: pageState.latestHistory.id,
          comment: pageState.latestHistory.comment,
          disease_tags: pageState.latestHistory.disease_tags
        } : null
      });
    }
  }, [horse, pageState]);
  
  // 馬IDをパース
  const horseId = useMemo(() => {
    try {
      const idParam = params?.id;
      if (!idParam || typeof idParam !== 'string' || idParam.trim() === '') {
        throw new Error('馬IDが指定されていません');
      }
      return idParam;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : '無効な馬IDです';
      console.error('馬IDのパースに失敗しました:', errorMessage);
      setError(errorMessage);
      setIsLoading(false);
      return '';
    }
  }, [params]);

  // データ取得
  useEffect(() => {
    if (!horseId) return;

    const fetchHorseData = async () => {
      console.log('Fetching horse data for ID:', horseId);
      setIsLoading(true);
      try {
        // 馬の基本データを取得
        const { horse: horseData, error } = await getHorseData(horseId);
        
        if (error) {
          throw new Error(error);
        }
        
        if (!horseData) {
          throw new Error('馬のデータが見つかりませんでした');
        }
        
        // オークション履歴を取得
        const auctionHistoriesData = await getAuctionHistories(horseId);
        
        // AuctionHistory を ExtendedAuctionHistory に変換
        const extendedAuctionHistories: ExtendedAuctionHistory[] = auctionHistoriesData.map(history => ({
          ...history,
          // sold_price を数値に変換（文字列の場合はパース、nullの場合はそのまま）
          sold_price: history.sold_price ? Number(history.sold_price) : null,
          // その他の必要なプロパティがあればここで追加
        }));
        
        // ExtendedAuctionHistory を AuctionHistory に変換
        const formattedAuctionHistories: AuctionHistory[] = extendedAuctionHistories.map(history => ({
          ...history,
          auction_date: history.auction_date,
          seller: history.seller || null
        }));
        
        // 馬データにオークション履歴をマージ
        const horseWithHistories: HorseWithPageProps = {
          ...horseData,
          auction_histories: formattedAuctionHistories,
          history: extendedAuctionHistories // 互換性のため
        };
        
        console.log('Fetched horse data with histories:', {
          id: horseWithHistories.id,
          name: horseWithHistories.name,
          auctionHistoriesCount: auctionHistoriesData.length,
          comment: horseWithHistories.comment,
          disease_tags: horseWithHistories.disease_tags,
          history: horseWithHistories.history?.length
        });
        
        // 状態を更新
        setHorse(horseWithHistories);
        
        // コメントがあるかチェック
        let hasAnyComment = false;
        let latestHistoryItem: ExtendedAuctionHistory | null = null;
        
        if (horseData.history?.length > 0) {
          hasAnyComment = horseData.history.some(h => h.comment && h.comment.trim() !== '');
          console.log('Has comments in history:', hasAnyComment);
          
          // 最新の履歴をセット（ソートして最新の1件を取得）
          const sortedHistory = [...horseData.history].sort((a, b) => {
            const dateA = Array.isArray(a.auction_date) ? a.auction_date[0] : a.auction_date || '';
            const dateB = Array.isArray(b.auction_date) ? b.auction_date[0] : b.auction_date || '';
            return new Date(dateB).getTime() - new Date(dateA).getTime();
          });
          
          latestHistoryItem = sortedHistory[0] || null;
          
          // ログ出力用の型ガード関数
          const isExtendedAuctionHistory = (item: any): item is ExtendedAuctionHistory => {
            return item !== null && typeof item === 'object' && 'id' in item;
          };
          
          if (isExtendedAuctionHistory(latestHistoryItem)) {
            console.log('Latest history:', {
              id: latestHistoryItem.id,
              comment: latestHistoryItem.comment,
              disease_tags: latestHistoryItem.disease_tags
            });
          } else {
            console.log('No history available or invalid history item');
          }
        }
        
        // 状態を一度に更新
        setPageState({
          hasComments: hasAnyComment,
          latestHistory: latestHistoryItem
        });
        
        setHorse(horseData);
        setError(null);
      } catch (err) {
        console.error('馬データの取得中にエラーが発生しました:', err);
        setError(err instanceof Error ? err.message : 'データの取得中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHorseData();
  }, [horseId]);

  // コメントの有無と最新履歴を計算
  const commentAndHistory = useMemo(() => {
    if (!horse) return { hasComments: false, latestHistory: null };
    
    const history = Array.isArray(horse.history) ? horse.history : [];
    const latest = history[0] || null;
    const hasAnyComments = history.some(h => h.comment?.trim().length > 0);
    
    return { hasComments: hasAnyComments, latestHistory: latest };
  }, [horse]);

  // コメントと最新履歴の状態を更新
  useEffect(() => {
    setPageState({
      hasComments: commentAndHistory.hasComments,
      latestHistory: commentAndHistory.latestHistory
    });
  }, [commentAndHistory]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return <SimpleError message={error} />;
  }

  if (!horse) {
    return <SimpleError message="馬のデータが見つかりませんでした" />;
  }
  
  // 必須フィールドのバリデーション
  if (!horse.name || !horse.primary_image || !horse.history?.length) {
    console.warn('不完全な馬データ:', horse);
  }
  
  // 馬詳細コンポーネントを表示
  const horseWithPageProps = (() => {
    return {
      ...horse,
      // 必須プロパティを上書き
      history: Array.isArray(horse.history) 
        ? horse.history.map(h => ({
            ...h,
            // ExtendedAuctionHistory に必要なプロパティを追加
            id: (h as any).id || `temp-${Date.now()}`,
            horse_id: (h as any).horse_id || horse.id || `temp-horse-${Date.now()}`,
            auction_date: h.auction_date || new Date().toISOString().split('T')[0],
            sold_price: h.sold_price ?? null,
            total_prize_start: (h as any).total_prize_start ?? 0,
            total_prize_latest: (h as any).total_prize_latest ?? 0,
            weight: h.weight ?? null,
            seller: (h as any).seller || '不明',
            is_unsold: (h as any).is_unsold || (h as any).unsold || false,
            comment: (h as any).comment || '',
            created_at: (h as any).created_at || new Date().toISOString(),
            // 拡張プロパティ
            name: (h as any).name || horse.name || '不明',
            sex: (h as any).sex || horse.sex || '不明',
            age: typeof (h as any).age === 'number' ? (h as any).age : (Number((h as any).age) || 0),
            race_record: (h as any).race_record || '未出走',
            detail_url: (h as any).detail_url || horse.detail_url || '',
            primary_image: (h as any).primary_image || horse.primary_image || '',
            disease_tags: Array.isArray((h as any).disease_tags) 
              ? (h as any).disease_tags 
              : (typeof (h as any).disease_tags === 'string' 
                  ? (h as any).disease_tags.split(',').filter(Boolean) 
                  : [])
          }))
        : [],
      // 必須プロパティを追加
      disease_tags: (() => {
        const tags = (horse as any).disease_tags || [];
        return Array.isArray(tags) 
          ? tags 
          : (typeof tags === 'string' 
              ? tags.split(',').filter(Boolean) 
              : []);
      })(),
      // 明示的に文字列に変換
      primary_image: (() => {
        const img = horse.primary_image || horse.image_url || '';
        // オブジェクトの場合は JSON 文字列化、それ以外は文字列に変換
        return img && typeof img === 'object' ? JSON.stringify(img) : String(img);
      })(),
      detail_url: horse.detail_url || '',
      // その他の必須プロパティ
      rakuten_url: (horse as any).rakuten_url || '',
      auction_url: (horse as any).auction_url || '',
      unsold_count: (horse as any).unsold_count || 0,
      dam_sire: (horse as any).dam_sire || horse.damsire || '不明'
    };
  })();
  
  return horse ? (
    <HorseDetailContent 
      horse={horse} 
      hasComments={pageState.hasComments}
      latestHistory={pageState.latestHistory}
    />
  ) : null;
}

// URLが有効かどうかをチェックする関数
const isValidUrl = (url?: string | null): boolean => {
  if (!url) return false;
  try {
    new URL(url);
    return true;
  } catch (e) {
    return false;
  }
};

const HorseDetailContent: React.FC<HorseDetailContentProps> = ({ 
  horse, 
  hasComments: hasCommentsInner, 
  latestHistory: latestHistoryInner 
}) => {
  // 引数名をリネームして、親コンポーネントの状態変数と競合しないようにする
  const hasComments = hasCommentsInner;
  const latestHistory = latestHistoryInner;

  useEffect(() => {
    console.log('馬データ:', JSON.stringify(horse, null, 2));
    console.log('JBIS URL:', horse?.jbis_url);
    console.log('Detail URL:', horse?.detail_url);
    console.log('Rakuten URL:', horse?.rakuten_url);
    console.log('Auction URL:', horse?.auction_url);
    console.log('All horse properties:', Object.keys(horse as object));
    console.log('楽天URL:', horse?.rakuten_url || horse?.detail_url);
  }, [horse]);

  // タブの状態管理（初期値は最後の履歴を指すように設定）
  const [activeTab, setActiveTab] = useState(0);

  // タブ変更ハンドラー
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // コメントがある履歴のインデックスを取得
  const commentIndices = useMemo(() => {
    if (!horse?.history?.length) return [];
    return horse.history
      .map((h, i) => (h.comment?.trim() ? i : -1))
      .filter(i => i !== -1);
  }, [horse?.history]);
  
  // 初期表示時に最後のコメントがあるタブを選択
  useEffect(() => {
    if (commentIndices.length > 0) {
      // 最後のコメントがあるインデックスを設定
      setActiveTab(commentIndices[commentIndices.length - 1]);
    }
  }, [commentIndices]);
  
  // 馬のデータがない場合のエラー表示
  if (!horse) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">馬のデータを読み込めませんでした</p>
          <Button component={Link} href="/" className="mt-4">
            トップに戻る
          </Button>
        </div>
      </div>
    );
  }

  // 最新の履歴は props から取得するため、ここでの宣言は不要
  // 有効な体重を取得（horse.weight を優先し、なければ最新履歴の weight を使用）
  const effectiveWeight = useMemo(() => {
    // デバッグ用に値を確認
    console.log('Raw weight values:', {
      horseWeight: horse.weight,
      historyWeight: latestHistory?.weight,
      horseWeightType: typeof horse.weight,
      historyWeightType: typeof latestHistory?.weight
    });

    // 数値に変換（余分な変換を避ける）
    const weight = horse.weight ?? latestHistory?.weight;

    console.log('Processed weight:', {
      value: weight,
      type: typeof weight,
      isNaN: weight !== null && weight !== undefined ? isNaN(Number(weight)) : 'undefined'
    });

    return weight;
  }, [horse.weight, latestHistory?.weight]);

  // 性別の色とアイコンをメモ化（互換性のため残すが、直接は使用しない）
  const { sexColor, sexIcon } = useMemo(() => {
    // 馬の基本情報から性別を取得（履歴がなければデフォルトで空文字）
    let sex = horse.sex || latestHistory?.sex || '';
    // 配列の場合は最初の要素を取得
    if (Array.isArray(sex)) {
      sex = sex[0] || '';
    }
    let color = 'text-white';
    let bgColor = 'bg-gray-200';
    let icon = '';

    if (sex === '牡' || sex === '牡馬') {
      bgColor = 'bg-blue-600';
      icon = '♂';
      sex = '牡';
    } else if (sex === '牝' || sex === '牝馬') {
      bgColor = 'bg-pink-500';
      icon = '♀';
      sex = '牝';
    } else if (sex === 'セ' || sex === 'せん' || sex === 'セン' || sex === 'せん馬') {
      bgColor = 'bg-green-600';
      color = 'text-white';
      icon = '⚥';
      sex = 'セ';
    }

    return { 
      sexColor: `text-white ${bgColor}`, // 常に白文字を強制
      sexIcon: icon 
    };
  }, [latestHistory?.sex]);

  // 画像URLを正規化（相対→絶対URL）
  const normalizedPrimaryImage = useMemo(() => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
    const raw = latestHistory?.primary_image as any;
    const src = typeof raw === 'string' ? raw : (raw && typeof raw.image_url === 'string' ? raw.image_url : '');
    return normalizeImageUrl(base, src);
  }, [latestHistory?.primary_image]);

  if (!latestHistory) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1, color: 'text-gray-900' }}>データが見つかりません</Typography>
          <p className="text-gray-600 mb-6">この馬の情報を取得できませんでした。</p>
          <Link href="/horses">
            <Button>馬一覧に戻る</Button>
          </Link>
        </div>
      </div>
    );
  }

  // 落札価格フォーマット（円単位で保存されているので、そのまま表示）
  // const formatPrice = (price: number) => {
  //   return price.toLocaleString();
  // };

  // タグをレンダリングする関数（string | string[] 双方に対応）
  const renderTags = (tags: string | string[]) => {
    if (!tags || (Array.isArray(tags) && tags.length === 0)) return null;
    const tagList: string[] = Array.isArray(tags)
      ? tags
      : tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);

    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {tagList.map((tag: string, index: number) => (
          <span key={index} className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">
            {tag}
          </span>
        ))}
      </div>
    );
  };

  // 以前の仕様に合わせた成長率計算
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <HeaderCard jbisUrl={horse.jbis_url} auctionUrl={horse.auction_url} />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* メイン情報 */}
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader 
                sx={{
                  padding: 0,
                  margin: 0,
                  '& .MuiCardHeader-content': {
                    padding: 0,
                    margin: 0
                  }
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1 }}>{latestHistory.name}</Typography>
                    {/* 性別・年齢 */}
                    <div className="flex items-center gap-2">
                      <SexBadge 
                        sex={horse.sex || latestHistory?.sex} 
                        age={latestHistory?.age ? Number(latestHistory.age) : undefined} 
                        className="text-xs"
                      />
                    </div>
                  </div>
                  {/* JBISリンク */}
                  {horse.jbis_url && (
                    <a
                      href={horse.jbis_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      JBIS
                    </a>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 馬名（カード内の上部に表示）と性別・年齢 */}
                  <div className="md:col-span-2 flex items-center gap-3">
                    <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem' }}>
                      {latestHistory.name}
                    </Typography>
                    {/* 性別バッジと年齢 */}
                    <SexBadge 
                      sex={horse.sex || latestHistory?.sex} 
                      age={latestHistory?.age ? Number(latestHistory.age) : undefined} 
                      className="text-xs"
                    />
                  </div>

                  {/* 左側: 画像とリンク */}
                  <div className="space-y-4">
                    {/* 画像は最新履歴から取得 */}
                    <div className="flex justify-center w-full h-64">
                      {latestHistory.primary_image ? (
                        <HorseImage
                          src={normalizedPrimaryImage}
                          alt={`${latestHistory.name}の画像`}
                          className="w-full h-full max-w-xs"
                        />
                      ) : (
                        <div className="w-full max-w-xs h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                          <div className="text-center text-gray-500">
                            <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            <p>画像なし</p>
                          </div>
                        </div>
                      )}
                    </div>
                    {/* 画像下のリンク（JBIS / サラオク / 楽天） */}
                    <div className="flex items-center justify-center">
                      <ExternalLinks 
                        jbisUrl={horse.jbis_url?.trim() || null}
                        auctionUrl={horse.detail_url?.trim() || null}
                        className="text-sm"
                      />
                    </div>
                  </div>

                  {/* 右側: 基本情報、血統、病歴 */}
                  <div className="space-y-4">
                    <div>
                      <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>基本情報</Typography>
                      <div className="space-y-2 text-sm">
                        {/* 体重表示 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">体重:</span>
                          <span className="font-medium">
                            {formatWeight(effectiveWeight)}
                          </span>
                        </div>
                        {/* 販売者履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">販売者:</span>
                          <span className="font-medium">{normalizeSeller(latestHistory.seller)}</span>
                        </div>
                        {/* レース成績履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">レース成績:</span>
                          <RaceRecordDisplay 
                            record={latestHistory.race_record} 
                            raceRecords={latestHistory.race_record} 
                          />
                        </div>
                        {/* 落札価格は右カラムに表示するため、このセクションでは非表示に変更 */}
                      </div>
                    </div>

                    {/* 血統・病歴はそのまま */}
                    <div>
                      <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>血統</Typography>
                      <div className="space-y-2 text-sm">
                        <div className="flex">
                          <span className="text-gray-600 w-12">父：</span>
                          <span className="font-medium text-left">{horse.sire || '-'}</span>
                        </div>
                        <div className="flex">
                          <span className="text-gray-600 w-12">母：</span>
                          <span className="font-medium text-left">{horse.dam || '-'}</span>
                        </div>
                        <div className="flex">
                          <span className="text-gray-600 w-12">母父：</span>
                          <span className="font-medium text-left">{horse.dam_sire || '-'}</span>
                        </div>
                      </div>
                    </div>

                    {/* 疾病タグ */}
                    <div className="mt-4">
                      {(() => {
                        // デバッグ用に horse オブジェクト全体を表示
                        console.log('horse オブジェクト:', JSON.stringify(horse, null, 2));
                        
                        // latestHistory?.disease_tags が配列でない場合に配列に変換
                        const historyDiseaseTags = latestHistory?.disease_tags 
                          ? Array.isArray(latestHistory.disease_tags) 
                            ? latestHistory.disease_tags 
                            : [latestHistory.disease_tags]
                          : [];
                        
                        // コメントを取得（horse.comment または latestHistory.comment から）
                        const comment = horse.comment || latestHistory?.comment || '';
                        
                        // 疾病タグを抽出（コメントからと既存のタグをマージ）
                        const extractedTags = extractDiseaseTags(
                          comment,
                          historyDiseaseTags.length > 0 ? historyDiseaseTags : (horse.disease_tags || [])
                        );
                        
                        console.log('コメント:', comment);
                        console.log('履歴の疾病タグ:', latestHistory?.disease_tags);
                        console.log('馬のデフォルト疾病タグ:', horse.disease_tags);
                        console.log('抽出されたタグ:', extractedTags);
                        
                        // テスト用のタグ（デバッグ用）
                        const testTags = ['テストタグ1', 'テストタグ2'];
                        
                        // 疾病タグがある場合のみ表示
                        if (extractedTags.length > 0) {
                          return (
                            <div className="mt-4">
                              <DiseaseTags 
                                tags={extractedTags}
                                className="mt-2"
                              />
                            </div>
                          );
                        }
                        
                        return null;
                      })()}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 履歴テーブル表示 */}
            <Card className="mb-6">
              <CardHeader 
                sx={{
                  padding: 0,
                  margin: 0,
                  '& .MuiCardHeader-content': {
                    padding: 0,
                    margin: 0
                  }
                }}
              >
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>全履歴</Typography>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm border">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-2 py-1 border">回</th>
                        <th className="px-2 py-1 border">日付</th>
                        <th className="px-2 py-1 border">馬名</th>
                        <th className="px-2 py-1 border">性</th>
                        <th className="px-2 py-1 border">年齢</th>
                        <th className="px-2 py-1 border">販売者</th>
                        <th className="px-2 py-1 border">成績</th>
                        <th className="px-2 py-1 border">落札価格</th>
                        <th className="px-2 py-1 border">落札時賞金</th>
                      </tr>
                    </thead>
                    <tbody>
                      {horse.history.map((h, i) => (
                        <tr key={i} className="border-b">
                          <td className="px-2 py-1 border text-center">{i + 1}</td>
                          <td className="px-2 py-1 border">
                            {Array.isArray(h.auction_date) ? h.auction_date[0] : h.auction_date}
                          </td>
                          <td className="px-2 py-1 border">{h.name}</td>
                          <td className="px-2 py-1 border text-black">
                            {(() => {
                              try {
                                const sex = Array.isArray(h.sex) ? h.sex[0] : h.sex || '';
                                if (typeof sex === 'string') {
                                  // ユニコードエスケープシーケンスをデコード
                                  return sex.replace(/\\u([\dA-Fa-f]{4})/g, (match, grp) => 
                                    String.fromCharCode(parseInt(grp, 16))
                                  ).replace(/[\"\[\]]/g, '');
                                }
                                return sex;
                              } catch (e) {
                                console.error('性別の表示中にエラーが発生しました:', e);
                                return '-';
                              }
                            })()}
                          </td>
                          <td className="px-2 py-1 border">{h.age}</td>
                          <td className="px-2 py-1 border">{normalizeSeller(h.seller)}</td>
                          <td className="px-2 py-1 border">
                            <RaceRecordDisplay 
                              record={h.race_record} 
                              raceRecords={h.race_record} 
                            />
                          </td>
                          <td className="px-2 py-1 border text-right">{
                            h.unsold || h.is_unsold || !h.sold_price ? '主取り' : formatCurrency(h.sold_price)
                          }</td>
                          <td className="px-2 py-1 border text-right">{formatPrizeMan(h.total_prize_start)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* コメント履歴（タブ切り替え） */}
            <CommentCard 
              history={horse.history}
              activeTab={activeTab}
              hasComments={hasComments}
              onTabChange={setActiveTab}
            />
          </div>

          {/* サイドバー - 価格・賞金情報 */}
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader 
                sx={{
                  padding: 0,
                  margin: 0,
                  '& .MuiCardHeader-content': {
                    padding: 0,
                    margin: 0
                  }
                }}
              >
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>落札価格</Typography>
              </CardHeader>
              <CardContent className="relative">
                {(() => {
                  if (process.env.NODE_ENV === 'development') {
                    console.log('latestHistory:', JSON.stringify({
                      sold_price: latestHistory?.sold_price,
                      unsold: latestHistory?.unsold,
                      history: latestHistory,
                      horse_history: horse.history
                    }, null, 2));
                  }
                  return null;
                })()}
                <div className="space-y-4">
                  {/* 主取り回数表示（1回以上の場合のみ表示） */}
                  {(horse.unsold_count ?? 0) > 0 && (
                    <div className="text-center text-blue-600 font-bold">主取り{horse.unsold_count}回</div>
                  )}
                  
                  {/* 落札価格 */}
                  <div className="text-center">
                    <div className="text-sm text-gray-600 mb-1">落札価格</div>
                    <div className="text-red-600 text-3xl font-extrabold">
                      {(() => {
                        // オークション履歴と同じロジックで表示
                        if (latestHistory?.unsold || latestHistory?.is_unsold || !latestHistory?.sold_price) {
                          return '主取り';
                        }
                        return formatCurrency(latestHistory.sold_price);
                      })()}
                    </div>
                  </div>
                </div>

                {/* 落札価格履歴 */}
                {horse.history.length > 1 && (
                  <div className="text-center mt-2">
                    <div className="text-sm text-gray-600 mb-2">落札価格履歴</div>
                    {horse.history
                      .filter((h, i) => {
                        // 有効な価格がある履歴のみを表示
                        const prices = toArray(h.sold_price)
                          .map(Number)
                          .filter(price => !isNaN(price) && price > 0);
                        return prices.length > 0;
                      })
                      .map((h, i, filteredHistory) => {
                        // 最新の有効な価格を取得
                        const prices = toArray(h.sold_price)
                          .map(Number)
                          .filter(price => !isNaN(price) && price > 0);
                        
                        if (prices.length === 0) return null;
                        
                        const latestPrice = prices[prices.length - 1];
                        const date = toArray(h.auction_date)[0] || '';
                        
                        // デバッグ用ログ
                        console.log('latestPrice:', {
                          value: latestPrice,
                          type: typeof latestPrice,
                          formatted: formatPrizeFromYen(latestPrice)
                        });
                        
                        return (
                          <div key={i} className="text-lg font-bold mb-1">
                            <span className="text-red-600">
                              {formatPrizeFromYen(latestPrice)}
                            </span>
                            {date && (
                              <span className="text-xs text-gray-500 ml-2">
                                {date}
                              </span>
                            )}
                          </div>
                        );
                      })}
                  </div>
                )}
              </CardContent>
            </Card>
            
            {/* 賞金情報カード */}
            <PrizeCard 
              horse={horse} 
              latestHistory={{ total_prize_start: latestHistory?.total_prize_start ?? null }} 
            /> 
            
            {/* 日付情報カード */}
            <DateInfoCard 
              auctionDate={latestHistory?.auction_date ? (Array.isArray(latestHistory.auction_date) ? latestHistory.auction_date[0] : latestHistory.auction_date) : ''}
              createdAt={horse.created_at || new Date().toISOString()}
              updatedAt={horse.updated_at}
            />
          </div>
        </div>
      </div>
    </div>
  );

  // 戻るボタンのレンダリング
  const renderBackButton = () => (
    <Button 
      variant="outlined" 
      size="small"
      onClick={() => window.history.back()}
      className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
    >
      戻る
    </Button>
  );

  // オークション履歴をレンダリング
  const renderAuctionHistory = () => {
    if (!horse?.history?.length) {
      return <p className="text-gray-500">オークション履歴がありません</p>;
    }

    // 型アサーションを使用して型エラーを解消
    const formattedHistory = horse.history.map(h => ({
      ...h,
      auction_date: h.auction_date || '',  // undefined の場合は空文字列を設定
      name: h.name || '',
      sex: h.sex || '',
      age: h.age || '',
      race_record: h.race_record || {},
    } as const));

    return (
      <AuctionHistoryCard 
        history={formattedHistory as any}  // 型アサーションを使用
        formatDate={formatDate}
        formatPrizeMan={formatPrizeMan}
      />
    );
  };

  // コメントセクションをレンダリング
  const renderCommentSection = () => {
    if (!hasComments) {
      return null;
    }

    return (
      <Card>
        <CardHeader>
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>オークションコメント</Typography>
        </CardHeader>
        <CardContent>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            sx={{ mb: 2 }}
            aria-label="horse detail tabs"
          >
            <Tab label="基本情報" />
            <Tab label="血統情報" />
            <Tab label="取引履歴" />
          </Tabs>
          {horse.history.map((h, i) => (
            <div key={i}>
              {h.comment ? (
                <div className="whitespace-pre-line p-4 bg-gray-50 rounded-md">
                  {h.comment}
                </div>
              ) : (
                <p className="text-gray-500">コメントがありません</p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    );
  };

  // メインのレンダリング
  return (
    <div className="container mx-auto px-4 py-8">
      {horse && (
        <HorseDetailContent 
          horse={horse}
          hasComments={hasComments}
          latestHistory={latestHistory}
        />
      )}
    </div>
  );
}