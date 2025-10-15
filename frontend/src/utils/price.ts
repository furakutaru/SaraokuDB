// 数値に変換するユーティリティ関数
export function toNumber(val: unknown): number | null {
  const n = Number(val);
  return Number.isFinite(n) ? n : null;
}

// 有効な正の数値かどうかをチェックする関数
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

// 履歴データの型定義
export interface HistoryLike {
  auction_date?: string;
  sold_price?: number | string | null;
  unsold?: boolean;
  is_unsold?: boolean | string;
}

// 馬データの型定義
export interface HorseLikeForPrice {
  unsold?: boolean;
  is_unsold?: boolean | string;
  sold_price?: number | string | null;
  history?: HistoryLike[];
  price?: number | string | null;
  effectiveAuction?: {
    sold_price?: number | string | null;
    is_unsold?: boolean;
    unsold?: boolean;
  };
  display_price?: string;
}

// 価格を表示用の文字列に変換する関数
export function getDisplayPrice(horse: HorseLikeForPrice | null | undefined): string {
  if (!horse) return '価格未設定';

  // 主取りの判定
  const isUnsold = horse.unsold === true ||
                 horse.is_unsold === true ||
                 (typeof horse.is_unsold === 'string' && horse.is_unsold.toLowerCase() === 'true') ||
                 horse.sold_price === null ||
                 horse.sold_price === undefined ||
                 horse.sold_price === '[null]' ||
                 horse.sold_price === 'null' ||
                 (horse.effectiveAuction && (horse.effectiveAuction.is_unsold || horse.effectiveAuction.unsold));

  if (isUnsold) {
    return '主取り';
  }

  // effectiveAuction から価格を取得
  if (horse.effectiveAuction && horse.effectiveAuction.sold_price) {
    const price = horse.effectiveAuction.sold_price;
    if (typeof price === 'number') {
      return formatPrice(price);
    } else if (typeof price === 'string') {
      const cleanPrice = price.replace(/[^0-9.-]/g, '');
      const numPrice = parseFloat(cleanPrice);
      if (!isNaN(numPrice) && numPrice > 0) {
        return formatPrice(numPrice);
      }
    }
  }

  // 配列の場合の処理（例: [1020000] のような形式）
  if (Array.isArray(horse.sold_price)) {
    // 配列内の最後の有効な価格を取得
    const lastValidPrice = horse.sold_price
      .map(price => {
        // 文字列の場合は数値に変換を試みる
        if (typeof price === 'string') {
          // 角括弧で囲まれた文字列を処理（例: "[1020000]"）
          const cleanPrice = price.replace(/[\[\]"\s]/g, '');
          // 数値に変換
          return parseFloat(cleanPrice) || null;
        }
        return Number(price) || null;
      })
      .filter((price): price is number => price !== null && !isNaN(price) && price > 0)
      .pop();

    if (lastValidPrice !== undefined) {
      return formatPrice(lastValidPrice);
    }
    return '主取り';
  }

  // 文字列の価格の場合（例: "310000" または "[310000]"）
  if (typeof horse.sold_price === 'string') {
    // 角括弧を削除
    const cleanPrice = horse.sold_price.replace(/[\[\]]/g, '');
    // 数値に変換
    const price = parseFloat(cleanPrice);
    
    if (!isNaN(price) && price > 0) {
      return formatPrice(price);
    }
    return '主取り';
  }
  
  // 数値の価格の場合
  if (typeof horse.sold_price === 'number') {
    return formatPrice(horse.sold_price);
  }

  // 履歴から価格を取得
  if (horse.history && horse.history.length > 0) {
    const latestHistory = horse.history[0];
    if (latestHistory) {
      // 履歴内の主取りフラグをチェック
      const isHistoryUnsold = latestHistory.unsold === true ||
                            latestHistory.is_unsold === true ||
                            (typeof latestHistory.is_unsold === 'string' && latestHistory.is_unsold.toLowerCase() === 'true');
      
      if (isHistoryUnsold) {
        return '主取り';
      }

      // 履歴内の価格をチェック
      if (latestHistory.sold_price) {
        if (Array.isArray(latestHistory.sold_price)) {
          const validPrices = latestHistory.sold_price
            .map(price => Number(price))
            .filter(price => !isNaN(price) && price > 0);
          
          if (validPrices.length > 0) {
            return formatPrice(validPrices[validPrices.length - 1]);
          }
        } else if (typeof latestHistory.sold_price === 'string') {
          const price = Number(latestHistory.sold_price.replace(/[^0-9.-]+/g, ''));
          if (!isNaN(price) && price > 0) {
            return formatPrice(price);
          }
        } else if (typeof latestHistory.sold_price === 'number' && latestHistory.sold_price > 0) {
          return formatPrice(latestHistory.sold_price);
        }
      }
    }
  }

  // トップレベルのpriceをチェック
  if (horse.price) {
    if (Array.isArray(horse.price)) {
      const validPrices = horse.price
        .map(price => Number(price))
        .filter(price => !isNaN(price) && price > 0);
      
      if (validPrices.length > 0) {
        return `¥${validPrices[validPrices.length - 1].toLocaleString()}`;
      }
    } else if (typeof horse.price === 'string') {
      const price = Number(horse.price.replace(/[^0-9.-]+/g, ''));
      if (!isNaN(price) && price > 0) {
        return `¥${price.toLocaleString()}`;
      }
    } else if (typeof horse.price === 'number' && horse.price > 0) {
      return formatPrice(horse.price);
    }
  }

  // デフォルト
  return '価格未設定';
}

export function formatPrice(val: number | string | null | undefined): string {
  // 値がnull、undefined、空文字の場合は'¥0'を返す
  if (val === null || val === undefined || val === '') {
    return '¥0';
  }

  // 数値の場合はそのままフォーマット
  if (typeof val === 'number') {
    return `¥${val.toLocaleString('ja-JP')}`;
  }

  // 文字列の場合は「万円」サフィックスを処理
  if (typeof val === 'string') {
    // 「万円」サフィックスを削除
    if (val.endsWith('万円')) {
      const numStr = val.replace(/[^0-9.-]/g, '');
      const numValue = parseFloat(numStr);
      if (!isNaN(numValue)) {
        // 10000をかけて円に変換
        return `¥${(numValue * 10000).toLocaleString('ja-JP')}`;
      }
    }
    // 通常の数値文字列の処理
    const numStr = val.replace(/[^0-9.-]/g, '');
    const numValue = parseFloat(numStr);
    if (!isNaN(numValue)) {
      return `¥${numValue.toLocaleString('ja-JP')}`;
    }
  }
  
  return '¥0';
}
