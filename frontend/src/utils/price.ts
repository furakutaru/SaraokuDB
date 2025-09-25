// Price display logic per spec (MEMORY: 落札価格表示ロジック仕様)
export function toNumber(val: unknown): number | null {
  const n = Number(val);
  return Number.isFinite(n) ? n : null;
}

export function isValidPositive(n: unknown): n is number {
  const num = Number(n);
  return Number.isFinite(num) && num > 0;
}

export interface HistoryLike {
  auction_date?: string;
  sold_price?: number | string | null;
}

export interface HorseLikeForPrice {
  unsold?: boolean;
  sold_price?: number | string | null;
  history?: HistoryLike[];
  price?: number | string | null;
}

export function getDisplayPrice(horse: HorseLikeForPrice): string {
  try {
    // 1) 主取りフラグ
    if (horse?.unsold === true) return '主取り';

    // 2) 馬オブジェクト直下
    if (isValidPositive(horse?.sold_price)) {
      return formatPrice(Number(horse!.sold_price));
    }

    // 3) 履歴から最新の有効価格
    if (Array.isArray(horse?.history) && horse!.history!.length > 0) {
      const sorted = [...horse!.history!].sort((a, b) => {
        const ad = new Date(a.auction_date || '').getTime();
        const bd = new Date(b.auction_date || '').getTime();
        return bd - ad;
      });
      const hit = sorted.find(h => isValidPositive(h.sold_price));
      if (hit) return formatPrice(Number(hit.sold_price));
    }

    // 4) トップレベル price
    if (isValidPositive(horse?.price)) {
      return formatPrice(Number(horse!.price));
    }

    // 5) デフォルト
    return '-';
  } catch {
    return '-';
  }
}

export function formatPrice(val: number): string {
  if (!isValidPositive(val)) return '主取り';
  // 円を前提にローカライズ
  return `¥${Number(val).toLocaleString('ja-JP')}`;
}
