'use client';

import { useState, useMemo, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { HeaderCard } from './components';
import ExternalLinks from './components/ExternalLinks';
import { ErrorMessage, SimpleError } from './components/ErrorDisplay';
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
import HorseImage from '@/src/components/HorseImage';
import { formatPrizeMan } from '@/src/utils/format';
import { normalizeImageUrl } from '@/src/utils/url';
import { Horse as BaseHorse, AuctionHistory as BaseHistory } from '@/src/types/horse';
import { getHorseData as getHorseDataFromApi } from '@/src/utils/horseApi';

// 馬体重をフォーマットする関数（整数値のみを想定）
function formatWeight(weight: number | string | null | undefined): string {
  if (weight === null || weight === undefined || weight === '') {
    return '-';
  }
  // 数値チェックのみ行い、そのまま表示
  return isNaN(Number(weight)) ? '-' : `${weight}kg`;
}
// --- 型定義（共有型に基づき最小拡張）---
// RaceRecord 型を文字列またはオブジェクトのユニオン型として定義
type RaceRecord = string | {
  total_races?: number;
  wins?: number;
  seconds?: number;  // 2着回数
  thirds?: number;   // 3着回数
  record_format?: string;
  formatted_record?: string;
  [key: string]: any; // その他のプロパティも許容
};

type HorseHistory = Omit<Partial<BaseHistory>, 'race_record'> & {
  name?: string;
  sex?: string;
  age?: string | number;
  race_record?: RaceRecord | string; // 文字列も受け入れる
  primary_image?: string;
  disease_tags?: string;
};

type Horse = Omit<Partial<BaseHorse>, 'age' | 'disease_tags'> & {
  id: string | number;
  auction_id?: string; // オークションID
  name: string; // 馬名
  sex: string; // 性別
  age: string | number; // 年齢（表示用）
  color: string; // 毛色
  birthday: string; // 生年月日
  history: HorseHistory[]; // オークション履歴
  sire: string; // 父
  dam: string; // 母
  dam_sire?: string; // 母の父（互換性のため残す）
  damsire?: string; // 母の父（新しい形式）
  primary_image: string; // メイン画像
  disease_tags: string[]; // 疾患タグ
  jbis_url: string; // JBISリンク
  rakuten_url?: string; // 楽天オークションリンク（優先）
  detail_url: string; // 楽天オークションリンク（旧形式、互換性のため）
  auction_url?: string; // オークションURL（旧形式、互換性のため）
  weight?: number; // 体重
  unsold_count?: number; // 未出走回数
  total_prize_latest: number; // 最新の賞金
  created_at: string;
  updated_at: string;
  unsold?: boolean; // 未出走フラグ
};
interface HorseData {
  metadata: any;
  horses: Horse[];
}

interface CommentedHistory extends HorseHistory {
  originalIndex: number;
}

interface HorseDetailContentProps {
  horse: Horse;
}

interface PageProps {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

// 日付フォーマット用のヘルパー関数
const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'yyyy年M月d日', { locale: ja });
  } catch (e) {
    return dateString; // 日付が不正な場合はそのまま返す
  }
};

// --- 追加ユーティリティ ---
const toArray = (val: any) => Array.isArray(val) ? val : [val];
const formatManYen = (val: number) => isNaN(val) ? '-' : `${(val/10000).toFixed(1)}万円`;

// 価格表示は utils/price の仕様化ロジックを使用（UIは変えない）

// 以前の仕様に合わせた成長率計算
const calculateGrowthRate = (start: number, latest: number) => {
  if (start === 0) return '-';
  const rate = ((latest - start) / start * 100).toFixed(1);
  return (latest - start >= 0 ? '+' : '') + rate;
};

// 賞金は万円単位で表示（共通ユーティリティを使用）

// ローディングコンポーネント
function LoadingSpinner() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
    </div>
  );
}

/**
 * 馬データを取得する関数
 * @param horseId 取得する馬のID
 * @returns 馬データとエラー情報を含むオブジェクト
 */
async function getHorseData(horseId: string): Promise<{ horse: Horse | null; error: string | null }> {
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
                  const historyEntry: HorseHistory = {
                    auction_date: staticBase.auction_date || new Date().toISOString().split('T')[0],
                    name: staticBase.name || '不明',
                    sex: staticBase.sex || '不明',
                    age: String(staticBase.age ?? '0'),
                    seller: staticBase.seller || '不明',
                    race_record: staticBase.race_record || '未出走',
                    comment: staticBase.comment || '',
                    sold_price: staticBase.sold_price ?? null,
                    total_prize_start: staticBase.total_prize_start ?? 0,
                    unsold: (staticBase.unsold ?? false) || (staticBase.is_unsold ?? false),
                    detail_url: staticBase.auction_url || '',
                    primary_image: staticBase.primary_image || staticBase.image_url || '',
                    disease_tags: Array.isArray(staticBase.disease_tags) ? staticBase.disease_tags.join(',') : (staticBase.disease_tags || ''),
                    weight: staticBase.weight
                  };

                  const horse: Horse = {
                    id: staticBase.id ?? horseId,
                    auction_id: staticBase.auction_id,
                    name: staticBase.name || '不明',
                    sex: staticBase.sex || '不明',
                    age: String(staticBase.age ?? '0'),
                    color: staticBase.color || '不明',
                    birthday: staticBase.birthday || '不明',
                    history: [historyEntry],
                    sire: staticBase.sire || '不明',
                    dam: staticBase.dam || '不明',
                    dam_sire: staticBase.dam_sire || staticBase.damsire || '不明',
                    damsire: staticBase.dam_sire || staticBase.damsire || '不明',
                    primary_image: staticBase.primary_image || staticBase.image_url || '',
                    disease_tags: Array.isArray(staticBase.disease_tags) ? staticBase.disease_tags : (staticBase.disease_tags || '').split(',').filter(Boolean),
                    jbis_url: staticBase.jbis_url || '',
                    detail_url: staticBase.detail_url || staticBase.auction_url || '',
                    rakuten_url: staticBase.detail_url || staticBase.auction_url || '',
                    auction_url: staticBase.detail_url || staticBase.auction_url || '',
                    weight: staticBase.weight,
                    unsold_count: staticBase.unsold_count || 0,
                    total_prize_latest: staticBase.total_prize_latest ?? 0,
                    created_at: staticBase.created_at || new Date().toISOString(),
                    updated_at: staticBase.updated_at || new Date().toISOString(),
                    unsold: (staticBase.unsold ?? false) || (staticBase.is_unsold ?? false)
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
          const historyEntry: HorseHistory = {
            auction_date: horseBaseData.auction_date || new Date().toISOString().split('T')[0],
            name: horseBaseData.name || '不明',
            sex: horseBaseData.sex || '不明',
            age: String(horseBaseData.age ?? '0'),
            seller: horseBaseData.seller || '不明',
            race_record: horseBaseData.race_record || '未出走',
            comment: horseBaseData.comment || '',
            sold_price: horseBaseData.sold_price ?? null,
            total_prize_start: horseBaseData.total_prize_start ?? 0,
            detail_url: horseBaseData.detail_url || horseBaseData.auction_url || '',
            unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false) || (horseBaseData.unsold_count > 0),
            detail_url: horseBaseData.auction_url || '',
            primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
            disease_tags: Array.isArray(horseBaseData.disease_tags) ? horseBaseData.disease_tags.join(',') : (horseBaseData.disease_tags || ''),
            weight: horseBaseData.weight
          };

          const horse: Horse = {
            id: horseBaseData.id ?? horseId,
            auction_id: horseBaseData.auction_id,
            name: horseBaseData.name || '不明',
            sex: horseBaseData.sex || '不明',
            age: String(horseBaseData.age ?? '0'),
            color: horseBaseData.color || '不明',
            birthday: horseBaseData.birthday || '不明',
            history: [historyEntry],
            sire: horseBaseData.sire || '不明',
            dam: horseBaseData.dam || '不明',
            dam_sire: horseBaseData.dam_sire || horseBaseData.damsire || '不明',
            damsire: horseBaseData.dam_sire || horseBaseData.damsire || '不明',
            primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
            disease_tags: Array.isArray(horseBaseData.disease_tags) ? horseBaseData.disease_tags : (horseBaseData.disease_tags || '').split(',').filter(Boolean),
            jbis_url: horseBaseData.jbis_url || '',
            detail_url: horseBaseData.detail_url || horseBaseData.auction_url || '',
            rakuten_url: horseBaseData.detail_url || horseBaseData.auction_url || '',
            auction_url: horseBaseData.detail_url || horseBaseData.auction_url || '',
            weight: horseBaseData.weight,
            unsold_count: horseBaseData.unsold_count || 0,
            total_prize_latest: horseBaseData.total_prize_latest ?? 0,
            created_at: horseBaseData.created_at || new Date().toISOString(),
            updated_at: horseBaseData.updated_at || new Date().toISOString(),
            unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false) || (horseBaseData.unsold_count > 0)
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
    
    // バックエンドの単体取得は Horse モデルを返す想定。
    // 既存UIが必要とするフィールドに合わせて最小限マッピング。
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

    const historyEntry: HorseHistory = {
      auction_date: horseBaseData.auction_date || new Date().toISOString().split('T')[0],
      name: horseBaseData.name || '不明',
      sex: horseBaseData.sex || '不明',
      age: String(horseBaseData.age ?? '0'),
      seller: horseBaseData.seller || '不明',
      race_record: horseBaseData.race_record || '未出走',
      comment: horseBaseData.comment || '',
      sold_price: horseBaseData.sold_price ?? null,
      total_prize_start: horseBaseData.total_prize_start ?? 0,
      unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false),
      detail_url: detailUrl,
      primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
      disease_tags: Array.isArray(horseBaseData.disease_tags) ? horseBaseData.disease_tags.join(',') : (horseBaseData.disease_tags || ''),
      weight: horseBaseData.weight
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

    const horse: Horse = {
      id: horseBaseData.id ?? horseId,
      auction_id: data?.auction_id || horseBaseData.auction_id, // APIレスポンスのルートからauction_idを取得
      name: horseBaseData.name || '不明',
      sex: horseBaseData.sex || '不明',
      age: String(horseBaseData.age ?? '0'),
      color: horseBaseData.color || '不明',
      birthday: horseBaseData.birthday || '不明',
      history: [historyEntry],
      sire: horseBaseData.sire || '不明',
      dam: horseBaseData.dam || '不明',
      dam_sire: horseBaseData.dam_sire || horseBaseData.damsire || '不明',
      damsire: horseBaseData.dam_sire || horseBaseData.damsire || '不明',
      primary_image: horseBaseData.primary_image || horseBaseData.image_url || '',
      disease_tags: Array.isArray(horseBaseData.disease_tags) 
        ? horseBaseData.disease_tags 
        : (horseBaseData.disease_tags || '').split(',').filter(Boolean),
      jbis_url: jbisUrl,
      // APIから受け取ったURLをそのまま使用
      detail_url: detailUrl,
      rakuten_url: rakutenUrl,
      auction_url: auctionUrl,
      weight: horseBaseData.weight,
      unsold_count: horseBaseData.unsold_count || 0,
      total_prize_latest: horseBaseData.total_prize_latest ?? 0,
      created_at: horseBaseData.created_at || new Date().toISOString(),
      updated_at: horseBaseData.updated_at || new Date().toISOString(),
      unsold: (horseBaseData.unsold ?? false) || (horseBaseData.is_unsold ?? false)
    };
    
    console.log('Debug - Mapped horse URLs:', {
      detail_url: horse.detail_url,
      rakuten_url: horse.rakuten_url,
      auction_url: horse.auction_url,
      jbis_url: horse.jbis_url
    });

    console.log('Debug - Generated horse object:', horse);
    
    // デバッグ用にマッピング後のデータをログ出力
    console.log('Debug - Mapped horse data:', {
      jbis_url: horse.jbis_url,
      auction_id: horse.auction_id,
      hasAuctionId: !!horse.auction_id
    });

    console.log('[horse detail] Mapped horse:', JSON.stringify({
      ...horse,
      // 大きなデータは省略
      history: horse.history?.map(h => ({
        ...h,
        // 履歴の詳細は省略
        auction_date: h.auction_date,
        sold_price: h.sold_price,
        detail_url: h.detail_url
      }))
    }, null, 2));
    return { horse, error: null };
  } catch (error) {
    console.error('馬データの取得中にエラーが発生しました:', error);
    return { 
      horse: null, 
      error: error instanceof Error ? error.message : '不明なエラーが発生しました' 
    };
  }
}

// シンプルなローディングコンポーネント
function SimpleLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );
}

// ページのパラメータ型
interface PageProps {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

// レース成績表示用のコンポーネント
const RaceRecordDisplay = ({ record }: { record: any }) => {
  try {
    // レコードが存在しない場合
    if (!record) return <span className="font-medium">データなし</span>;
    
    // 文字列の場合
    if (typeof record === 'string') {
      // JSON文字列の可能性がある場合
      if (record.startsWith('{') && record.endsWith('}')) {
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
    
    return <span className="font-medium">データなし</span>;
  } catch (e) {
    console.error('レース成績の表示中にエラーが発生しました:', e);
    return <span className="font-medium">データなし</span>;
  }
};

// ページコンポーネント (Client Component)
export default function HorseDetailPage({ params }: PageProps) {
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<number>(0);
  
  // 馬IDをパース (Next.js 14+ のparams Promise対応)
  const horseId = useMemo(() => {
    try {
      const idParam = params?.id;
      if (!idParam || typeof idParam !== 'string' || idParam.trim() === '') {
        throw new Error('馬IDが指定されていません');
      }
      return idParam;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : '無効な馬IDです';
      setError(errorMessage);
      setIsLoading(false);
      console.error('馬IDのパースに失敗しました:', errorMessage);
      return '';
    }
  }, [params]);
  
  // コメントの有無をチェック
  const hasComments = useMemo(() => {
    if (!horse?.history) return false;
    return horse.history.some(history => 
      history.comment && history.comment.trim().length > 0
    );
  }, [horse]);
  
  // データ取得とエラー処理
  useEffect(() => {
    const fetchHorseData = async () => {
      if (!horseId) {
        setError('馬IDが指定されていません');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const { horse, error } = await getHorseData(horseId);
        
        if (error) {
          throw new Error(error);
        } 
        
        if (!horse) {
          throw new Error('馬のデータが見つかりませんでした');
        }

        // 必須フィールドのバリデーション
        if (!horse.name || !horse.primary_image || !horse.history?.length) {
          console.warn('不完全な馬データ:', horse);
        }

        // disease_tags をこのページの型に合わせて補正
        const fixedHorse = {
          ...horse,
          disease_tags: Array.isArray((horse as any).disease_tags)
            ? (horse as any).disease_tags
            : (typeof (horse as any).disease_tags === 'string'
                ? ((horse as any).disease_tags as string).split(',').map(s => s.trim()).filter(Boolean)
                : []),
        } as Horse;
        setHorse(fixedHorse);
      } catch (err) {
        console.error('馬データの取得中にエラーが発生しました:', err);
        setError(err instanceof Error ? err.message : 'データの取得中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHorseData();
  }, [horseId]);
  
  if (isLoading) {
    return <SimpleLoading />;
  }
  
  if (error) {
    return <SimpleError message={error} />;
  }
  
  if (!horse) {
    return <SimpleError message="馬のデータが見つかりませんでした" />;
  }
  
  // 馬詳細コンポーネントを表示
  return <HorseDetailContent horse={horse} />;
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

const HorseDetailContent: React.FC<HorseDetailContentProps> = ({ horse }) => {
  useEffect(() => {
    console.log('馬データ:', JSON.stringify(horse, null, 2));
    console.log('JBIS URL:', horse?.jbis_url);
    console.log('Detail URL:', horse?.detail_url);
    console.log('Rakuten URL:', horse?.rakuten_url);
    console.log('Auction URL:', horse?.auction_url);
    console.log('All horse properties:', Object.keys(horse as object));
    console.log('楽天URL:', horse?.rakuten_url || horse?.detail_url);
  }, [horse]);

  // タブの状態管理
  const [activeTab, setActiveTab] = useState(0);

  // タブ変更ハンドラー
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // コメントの有無をチェック
  const hasComments = useMemo(() => {
    return horse?.history?.some(h => h.comment?.trim()) || false;
  }, [horse?.history]);
  
  // コメントがある履歴のみをフィルタリング
  const tabsWithComments = useMemo<CommentedHistory[]>(() => {
    if (!horse?.history?.length) return [];
    return horse.history.reduce<CommentedHistory[]>((acc, history, index) => {
      if (history.comment?.trim()) {
        acc.push({ ...history, originalIndex: index });
      }
      return acc;
    }, []);
  }, [horse?.history]);
  
  // 初期表示時に最初のコメントがあるタブを選択
  useEffect(() => {
    if (tabsWithComments.length > 0) {
      setActiveTab(tabsWithComments[0].originalIndex);
    }
  }, [tabsWithComments]);
  
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

  // 最新の履歴をメモ化
  const latestHistory = useMemo(() => {
    if (!horse.history || horse.history.length === 0) return null;
    return horse.history[horse.history.length - 1];
  }, [horse.history]);

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

  // 性別の色とアイコンをメモ化
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
                      <Badge className={sexColor}>
                        {Array.isArray(horse.sex) ? horse.sex[0] : (horse.sex || latestHistory?.sex || '')} {latestHistory?.age}歳
                      </Badge>
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
                    {/* 性別バッジ */}
                    <span className={`px-2 py-0.5 rounded-full text-xs ${sexColor}`}>
                      {Array.isArray(horse.sex) ? horse.sex[0] : (horse.sex || latestHistory?.sex || '')}
                    </span>
                    {/* 年齢 */}
                    <span className="text-sm text-gray-700">{latestHistory?.age}歳</span>
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
                    {/* 画像下のリンク（JBIS / サラオク） */}
                    <div className="flex items-center justify-center">
                      {console.log('Horse URLs:', {
                        jbis_url: horse.jbis_url,
                        detail_url: horse.detail_url,
                        rakuten_url: horse.rakuten_url,
                        auction_url: horse.auction_url
                      })}
                      <ExternalLinks 
                        jbisUrl={horse.jbis_url}
                        auctionUrl={horse.auction_url}
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
                          <span className="font-medium">{toArray(latestHistory.seller).join(' / ')}</span>
                        </div>
                        {/* オークション日履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">オークション日:</span>
                          <span className="font-medium">{toArray(latestHistory.auction_date).join(' / ')}</span>
                        </div>
                        {/* レース成績履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">レース成績:</span>
                          <RaceRecordDisplay record={latestHistory.race_record} />
                        </div>
                        {/* 落札価格は右カラムに表示するため、このセクションでは非表示に変更 */}
                        {/* オークションページリンク */}
                        {latestHistory.detail_url && (
                          <div className="flex justify-between items-center mt-2">
                            <span className="text-gray-600">オークションページ:</span>
                            <a
                              href={latestHistory.detail_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline text-sm flex items-center"
                            >
                              詳細を見る
                              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          </div>
                        )}
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

                    {/* 病歴（血統の下に1箇所のみ表示） */}
                    {((latestHistory.disease_tags && String(latestHistory.disease_tags).trim() !== '') ||
                      (horse.disease_tags && String(horse.disease_tags).trim() !== '')) && (
                      <div>
                        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>病歴</Typography>
                        <div className="flex flex-wrap gap-2">
                          {(() => {
                            try {
                              // 最新の履歴からタグを取得、なければ馬の基本情報から取得
                              const tags = latestHistory.disease_tags || horse.disease_tags || [];
                              
                              // タグを処理するヘルパー関数
                              const processTag = (tag: any) => {
                                if (tag === null || tag === undefined) return '';
                                if (typeof tag !== 'string') return String(tag);
                                
                                // ユニコードエスケープシーケンスをデコード
                                return tag
                                  .replace(/[\"\[\]]/g, '') // 余分な文字を削除
                                  .replace(/\\u([\dA-Fa-f]{4})/g, (match, grp) => 
                                    String.fromCharCode(parseInt(grp, 16))
                                  );
                              };
                              
                              // タグを処理
                              let processedTags: string[] = [];
                              
                              if (Array.isArray(tags)) {
                                processedTags = tags.map(processTag).filter(Boolean);
                              } else if (typeof tags === 'string') {
                                // 文字列をカンマで分割し、各タグを処理
                                processedTags = tags.split(',')
                                  .map(tag => processTag(tag.trim()))
                                  .filter(Boolean);
                              }
                              
                              // タグを表示
                              return processedTags.map((tag, index) => (
                            
                                <Badge key={index} variant="standard" className="bg-red-100 text-red-800 px-2 py-1 rounded">
                                  {tag}
                                </Badge>
                              ));
                            } catch (e) {
                              console.error('病歴の表示中にエラーが発生しました:', e);
                              return null;
                            }
                          })()}
                        </div>
                      </div>
                    )}
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
                          <td className="px-2 py-1 border">{h.auction_date}</td>
                          <td className="px-2 py-1 border">{h.name}</td>
                          <td className="px-2 py-1 border">
                            {Array.isArray(h.sex) ? h.sex[0] : (h.sex || '')}
                          </td>
                          <td className="px-2 py-1 border">{h.age}</td>
                          <td className="px-2 py-1 border">{h.seller}</td>
                          <td className="px-2 py-1 border"><RaceRecordDisplay record={h.race_record} /></td>
                          <td className="px-2 py-1 border text-right">{
                            h.unsold ? '不成立' : formatPrizeMan(h.sold_price || 0)
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
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>コメント履歴</Typography>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 mb-2 overflow-x-auto pb-2">
                  {horse.history.map((h, i) => {
                    const hasComment = h.comment && h.comment.trim() !== '';
                    return (
                      <button
                        key={i}
                        className={`px-3 py-1 rounded whitespace-nowrap ${
                          activeTab === i 
                            ? 'bg-blue-600 text-white' 
                            : hasComment 
                              ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' 
                              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                        onClick={() => setActiveTab(i)}
                        disabled={!hasComment}
                      >
                        {i + 1}回目 {!hasComment && '(コメントなし)'}
                      </button>
                    );
                  })}
                </div>
                <div className="border p-4 bg-gray-50 rounded-b min-h-[100px]">
                  {hasComments ? (
                    horse.history[activeTab]?.comment && horse.history[activeTab].comment.trim() !== '' ? (
                      <div className="prose max-w-none">
                        <p className="whitespace-pre-line text-gray-800">
                          {horse.history[activeTab].comment}
                        </p>
                        <div className="mt-2 text-sm text-gray-500">
                          {toArray(horse.history[activeTab]?.auction_date).join(' / ')}
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <p className="text-gray-500 italic">この回のコメントはありません</p>
                      </div>
                    )
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-gray-500 italic">この馬のコメントは登録されていません</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
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
                  
                  {/* 落札価格（最新） */}
                  <div className="text-center">
                    <div className="text-sm text-gray-600 mb-1">落札価格</div>
                    <div className="text-red-600 text-3xl font-extrabold">
                      {(() => {
                      // 主取りの場合は「主取り」と表示
                      if (latestHistory?.unsold || 
                          latestHistory?.sold_price === null ||
                          latestHistory?.sold_price === '[null]' || 
                          latestHistory?.sold_price === 'null') {
                        return '主取り';
                      }
                      
                      // sold_price が配列の場合は最後の有効な価格を使用
                      if (Array.isArray(latestHistory?.sold_price)) {
                        const validPrices = latestHistory.sold_price
                          .map(price => Number(price))
                          .filter(price => !isNaN(price) && price > 0);
                        
                        if (validPrices.length > 0) {
                          return `¥${validPrices[validPrices.length - 1].toLocaleString()}`;
                        }
                      } 
                      // sold_price が文字列の場合
                      else if (typeof latestHistory?.sold_price === 'string') {
                        // "[null]" または "null" の場合は主取りと表示
                        if (latestHistory.sold_price === '[null]' || latestHistory.sold_price === 'null') {
                          return '主取り';
                        }
                        // 数値に変換可能な場合は数値として表示
                        const price = Number(latestHistory.sold_price.replace(/[^0-9.-]+/g, ''));
                        if (!isNaN(price) && price > 0) {
                          return `¥${price.toLocaleString()}`;
                        }
                      }
                      // sold_price が数値の場合
                      else if (latestHistory?.sold_price) {
                        const price = Number(latestHistory.sold_price);
                        if (!isNaN(price) && price > 0) {
                          return `¥${price.toLocaleString()}`;
                        }
                      }
                      
                      // 上記のいずれにも該当しない場合は価格未設定
                      return '価格未設定';
                      })()}
                    </div>
                  </div>
                </div>
                {/* 履歴が2回以上ある場合のみ履歴表示 */}
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
                        
                        return (
                          <div key={i} className="text-lg font-bold mb-1">
                            <span className="text-red-600">
                              ¥{latestPrice.toLocaleString()}
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
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>賞金情報</Typography>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrizeMan(Number(latestHistory?.total_prize_start ?? 0))}
                    </div>
                    <div className="text-xs text-gray-600">落札時</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrizeMan(Number(horse.total_prize_latest))}
                    </div>
                    <div className="text-xs text-gray-600">現在</div>
                  </div>
                </div>
                <div className="border-t pt-4">
                  <div className="text-center">
                    <div className={`text-xl font-bold ${horse.total_prize_latest - (latestHistory?.total_prize_start ?? 0) > 0 ? 'text-green-600' : horse.total_prize_latest - (latestHistory?.total_prize_start ?? 0) < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {(() => {
                        const start = Number(latestHistory.total_prize_start ?? 0);
                        const latestPrize = Number(horse.total_prize_latest ?? 0);
                        const diff = latestPrize - start;
                        if (diff === 0) {
                          return '0万円';
                        } else if (diff > 0) {
                          return `+${formatManYen(diff)}`;
                        } else {
                          return `-${formatManYen(Math.abs(diff))}`;
                        }
                      })()}
                    </div>
                    <div className="text-sm text-gray-600">オークション後の活躍</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* データ更新日 */}
            <Card sx={{ '& .MuiCardHeader-root': { padding: 0, margin: 0 } }}>
              <CardHeader>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>データ情報</Typography>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">オークション日:</span>
                  <span>{formatDate(latestHistory?.auction_date || '')}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">作成日:</span>
                  <span>{formatDate(horse.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">更新日:</span>
                  <span>{formatDate(horse.updated_at)}</span>
                </div>

              </CardContent>
            </Card>
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

    return (
      <div className="space-y-4">
        {horse.history.map((history, index) => (
          <div key={index} className="border-b pb-4 last:border-b-0 last:pb-0">
            <div className="flex justify-between items-start">
              <div>
                <Typography variant="h6" component="h4" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>{formatDate(history.auction_date || '')}</Typography>
                <p className="text-sm text-gray-500">
                  落札価格: {history.unsold ? '不成立' : formatPrizeMan(history.sold_price || 0)}
                </p>
              </div>
              {history.detail_url && (
                <Button 
                  component={Link}
                  href={history.detail_url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  variant="outlined" 
                  size="small"
                  className="whitespace-nowrap"
                >
                  詳細を見る
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
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

  // URLが有効かどうかをチェックするヘルパー関数
  const isValidUrl = (url: string | undefined | null): boolean => {
    if (!url) return false;
    const trimmed = url.trim();
    return trimmed.length > 0 && trimmed !== 'undefined' && trimmed !== 'null';
  };

  // 馬の基本情報セクション
  const renderBasicInfo = () => {
    if (!horse) return null;
    
    // デバッグ用に現在のURLをログ出力
    console.log('Debug - Current horse data:', {
      jbis_url: horse.jbis_url,
      rakuten_url: horse.rakuten_url,
      detail_url: horse.detail_url,
      auction_url: horse.auction_url,
      auction_id: horse.id, // オークションIDを確認
      all_props: Object.keys(horse) // 利用可能なプロパティを確認
    });
    
    // デバッグ用に現在のデータをログ出力
    console.log('Debug - Building URLs with data:', {
      horseId: horse.id,
      auction_id: horse.auction_id,
      jbis_url: horse.jbis_url,
      rakuten_url: horse.rakuten_url,
      detail_url: horse.detail_url,
      auction_url: horse.auction_url
    });

    // JBIS URLを構築
    // データベースから取得したURLを使用
    const jbisUrl = horse.jbis_url?.trim() || '';
    const rakutenUrl = horse.auction_url?.trim() || '';
    
    console.log('Using URLs from database:', { 
      jbisUrl, 
      rakutenUrl, 
      hasJbisUrl: !!horse.jbis_url,
      hasAuctionUrl: !!horse.auction_url
    });
    
    return (
      <Card className="mb-6">
        <CardHeader>
          <div className="flex justify-between items-start w-full">
            <div>
              <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1 }}>{horse.name}</Typography>
              <Typography variant="body2" color="text.secondary" className="mb-2">
                {Array.isArray(horse.sex) ? horse.sex[0] : (horse.sex || '')} {horse.age}歳 | {horse.color} | {format(new Date(horse.birthday), 'yyyy年M月d日', { locale: ja })}
              </Typography>
              <div className="flex space-x-2 mt-2">
                {jbisUrl && (
                  <a 
                    href={jbisUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-full hover:bg-blue-700 transition-colors"
                  >
                    JBIS
                  </a>
                )}
                {rakutenUrl && (
                  <a 
                    href={rakutenUrl} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="px-3 py-1 bg-red-500 text-white text-sm font-medium rounded-full hover:bg-red-600 transition-colors"
                  >
                    サラオク
                  </a>
                )}
              </div>
            </div>
            <div className="flex space-x-2">
              {renderBackButton()}
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  };

  // メインのレンダリング
  return (
    <div className="container mx-auto px-4 py-8">
      {renderBasicInfo()}
      
      {/* 馬の詳細情報セクション */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 左カラム: 馬の画像 */}
        <div className="md:col-span-1">
          <Card className="mb-6">
            <div className="relative aspect-square">
              <HorseImage 
                src={horse.primary_image} 
                alt={horse.name}
                className="w-full h-full object-cover"
              />
            </div>
            <CardContent className="p-4">
              <div className="space-y-2">
                <div>
                  <span className="text-sm text-gray-500">父:</span>
                  <p className="font-medium">{horse.sire}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">母:</span>
                  <p className="font-medium">{horse.dam}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">母の父:</span>
                  <p className="font-medium">{horse.dam_sire}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* 右カラム: 馬の情報 */}
        <div className="md:col-span-2">
          {/* オークション履歴 */}
          <Card className="mb-6">
            <CardHeader>
              <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>オークション履歴</Typography>
            </CardHeader>
            <CardContent>
              {renderAuctionHistory()}
            </CardContent>
          </Card>
          
          {/* コメントセクション */}
          {renderCommentSection()}
        </div>
      </div>
    </div>
  );
}