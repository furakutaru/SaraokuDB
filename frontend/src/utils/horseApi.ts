import { matchHorseCandidate, normalizeId, normalizeName } from './ids';
import { buildUIHorse, HorseUI } from './horseMap';

// Types aligned with current pages (keep UI contracts unchanged)
export interface HorseHistoryUI {
  auction_date: string;
  name: string;
  sex: string;
  age: string;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number | null;
  total_prize_start: number;
  unsold?: boolean;
  detail_url?: string;
  primary_image?: string;
  disease_tags?: string;
  weight?: number;
}

// HorseUI is imported from horseMap

export interface HorsesListResponse {
  horses: any[];
  auctionHistories: any[];
  metadata: {
    last_updated: string;
    total_horses: number;
    total_auction_records: number;
  };
}

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
}

export async function fetchHorsesList(): Promise<HorsesListResponse> {
  const url = `${apiBase()}/api/horses?_=${Date.now()}`;
  console.log('[horseApi] fetch list:', url);
  const res = await fetch(url, { headers: { Accept: 'application/json' }, cache: 'no-store' });
  if (!res.ok) {
    const text = await res.text();
    console.error('[horseApi] list error', res.status, text);
    throw new Error('データの取得に失敗しました');
  }
  const data = await res.json();
  const horses = Array.isArray(data?.horses) ? data.horses : [];
  const auctionHistories = Array.isArray(data?.auctionHistories) ? data.auctionHistories : [];
  return {
    horses,
    auctionHistories,
    metadata: data?.metadata || {
      last_updated: new Date().toISOString(),
      total_horses: horses.length,
      total_auction_records: auctionHistories.length,
    },
  };
}

// buildUIHorse is imported

export async function getHorseData(horseIdRaw: string): Promise<{ horse: HorseUI | null; error: string | null }> {
  const horseId = normalizeId(horseIdRaw);
  if (!horseId) return { horse: null, error: '無効な馬IDです' };

  const detailUrl = `${apiBase()}/api/horses/${encodeURIComponent(horseId)}?_=${Date.now()}`;
  console.log('[horseApi] fetch detail:', detailUrl);
  const res = await fetch(detailUrl, { headers: { Accept: 'application/json' }, cache: 'no-store' });
  if (res.ok) {
    const base = await res.json();
    return { horse: buildUIHorse(base, horseId), error: null };
  }

  if (res.status !== 404) {
    const text = await res.text();
    console.error('[horseApi] detail error:', res.status, text);
    return { horse: null, error: '馬データの取得に失敗しました' };
  }

  // Fallback: list
  const listUrl = `${apiBase()}/api/horses?limit=10000&_=${Date.now()}`;
  console.warn('[horseApi] 404 → fallback list:', listUrl);
  const listRes = await fetch(listUrl, { headers: { Accept: 'application/json' }, cache: 'no-store' });
  if (listRes.ok) {
    const list = await listRes.json();
    const horses: any[] = Array.isArray(list?.horses) ? list.horses : [];
    const numId = Number(horseId);
    let candidate = horses.find(h => (
      h.id === horseId || (typeof h.id === 'number' && !Number.isNaN(numId) && h.id === numId) ||
      (h.auction_id && String(h.auction_id) === horseId)
    ));

    if (!candidate) {
      try {
        const staticUrl = (typeof window !== 'undefined')
          ? new URL('/data/horses.json', window.location.origin).toString()
          : '/data/horses.json';
        const staticRes = await fetch(staticUrl, { cache: 'no-store' });
        if (staticRes.ok) {
          const staticHorses = await staticRes.json();
          const staticBase = Array.isArray(staticHorses)
            ? staticHorses.find((h: any) => String(h.id) === horseId || String(h.auction_id) === horseId)
            : null;
          const baseName = staticBase?.name;
          const baseAge = staticBase?.age;
          if (baseName) {
            candidate = horses.find(h => matchHorseCandidate(h, horseId, baseName, baseAge))
              || horses.find(h => matchHorseCandidate(h, horseId, baseName, null));
          }
        }
      } catch (e) {
        console.warn('[horseApi] static lookup failed:', e);
      }
    }

    if (candidate) {
      return { horse: buildUIHorse(candidate, horseId), error: null };
    }

    // Last resort: static only
    try {
      const staticUrl = (typeof window !== 'undefined')
        ? new URL('/data/horses.json', window.location.origin).toString()
        : '/data/horses.json';
      const staticRes = await fetch(staticUrl, { cache: 'no-store' });
      if (staticRes.ok) {
        const staticHorses = await staticRes.json();
        const staticBase = Array.isArray(staticHorses)
          ? staticHorses.find((h: any) => String(h.id) === horseId || String(h.auction_id) === horseId)
          : null;
        if (staticBase) return { horse: buildUIHorse(staticBase, horseId), error: null };
      }
    } catch (e) {
      console.warn('[horseApi] static-only failed:', e);
    }

    const text = await res.text();
    console.error('[horseApi] not found after fallback:', text);
    return { horse: null, error: '馬データの取得に失敗しました' };
  }

  const text = await res.text();
  console.error('[horseApi] detail fetch error:', res.status, text);
  return { horse: null, error: '馬データの取得に失敗しました' };
}
