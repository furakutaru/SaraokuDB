// Price display logic per spec (MEMORY: 落札価格表示ロジック仕様)
export function toNumber(val: unknown): number | null {
  const n = Number(val);
  return Number.isFinite(n) ? n : null;
}

export function isValidPositive(n: unknown): n is number {
  if (Array.isArray(n) && n.length > 0) {
    // 配列の場合は最後の要素をチェック
    const last = n[n.length - 1];
    const num = Number(last);
    return Number.isFinite(num) && num > 0;
  }
  
  const num = Number(n);
  return Number.isFinite(num) && num > 0;
}

export interface HistoryLike {
  auction_date?: string;
  sold_price?: number | string | null;
}

export interface HorseLikeForPrice {
  unsold?: boolean;
  is_unsold?: boolean;
  sold_price?: number | string | null;
  history?: HistoryLike[];
  price?: number | string | null;
}

export function getDisplayPrice(horse: HorseLikeForPrice): string {
  try {
    // 1) 主取りフラグがtrueの場合は「主取り」を返す
    if (horse?.unsold === true || horse?.is_unsold === true) return '主取り';

    // 2) 馬オブジェクト直下の価格を確認
    if (horse?.sold_price !== undefined && horse.sold_price !== null) {
      // 配列の場合（例："[300000]"）の処理を追加
      if (Array.isArray(horse.sold_price) && horse.sold_price.length > 0) {
        const priceStr = String(horse.sold_price[0]).replace(/[^\d]/g, '');
        const price = Number(priceStr);
        if (!isNaN(price) && price > 0) {
          return formatPrice(price);
        }
      }
      // 数値の場合はそのままフォーマット
      else if (typeof horse.sold_price === 'number' && horse.sold_price > 0) {
        return formatPrice(horse.sold_price);
      }
      // 文字列の場合は数値に変換してフォーマット
      else if (typeof horse.sold_price === 'string') {
        const price = Number(horse.sold_price.replace(/[^\d]/g, ''));
        if (!isNaN(price) && price > 0) {
          return formatPrice(price);
        }
      }
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
  // 円を前提にローカライズ
  return `¥${Number(val).toLocaleString('ja-JP')}`;
}
