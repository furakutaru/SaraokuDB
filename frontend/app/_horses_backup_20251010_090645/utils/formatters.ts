import { Horse } from '../types';
import { formatAge } from './formatAge';

// Horse型を拡張してunsoldプロパティを追加
declare module '../types' {
  interface Horse {
    unsold?: boolean;
  }
}

/**
 * 主取りフラグをチェックするヘルパー関数
 * @param horse 馬のデータ
 * @returns 主取りの場合はtrue、それ以外はfalse
 */
export const isUnsoldHorse = (horse: Horse): boolean => {
  // sold_priceがnull、undefined、'[null]'、'null'、または数値の0以下の場合は主取りとみなす
  const isSoldPriceInvalid = 
    horse.sold_price === null ||
    horse.sold_price === undefined ||
    (typeof horse.sold_price === 'string' && 
      (horse.sold_price === '[null]' || horse.sold_price === 'null' || horse.sold_price === '')) ||
    (typeof horse.sold_price === 'number' && horse.sold_price <= 0);

  return (
    horse.unsold === true || // unsoldがtrueの場合
    horse.is_unsold === true || // is_unsoldがtrueの場合
    isSoldPriceInvalid
  );
};

/**
 * 価格を表示用にフォーマットする関数
 * @param price 価格（数値または文字列）
 * @returns フォーマットされた価格文字列
 */
export const formatPrice = (price: any): string => {
  if (price === null || price === undefined) return '-';
  
  // 数値に変換
  let priceValue: number;
  if (typeof price === 'string') {
    // 角括弧を削除してから数値に変換
    const cleanPrice = price.replace(/[\[\]"]/g, '');
    priceValue = parseFloat(cleanPrice);
  } else if (typeof price === 'number') {
    priceValue = price;
  } else {
    return '-';
  }

  // 数値が有効でない、または0以下の場合はハイフンを返す
  if (isNaN(priceValue) || priceValue <= 0) {
    return '-';
  }

  // 3桁区切りの数値にフォーマット
  return `¥${priceValue.toLocaleString()}`;
};

// formatAge is now imported from './formatAge'

/**
 * 売り主情報を適切に表示するためのヘルパー関数
 * @param seller 売り主情報
 * @returns フォーマットされた売り主情報
 */
export const formatSeller = (seller: any): string => {
  if (!seller) return '-';
  // 不要な接頭辞を削除
  return seller.replace(/^（(.*?)）$/, '$1').trim();
};

/**
 * 賞金を表示用にフォーマットする関数
 * @param val 賞金の値
 * @returns フォーマットされた賞金文字列
 */
export const formatPrize = (val: number | string | null | undefined): string => {
  if (val === null || val === undefined || val === '' || isNaN(Number(val))) return '-';
  return `${Number(val).toFixed(1)}万円`;
};

/**
 * 成長率を計算する関数
 * @param start 開始値
 * @param latest 最新値
 * @returns 成長率（パーセント）の文字列表現
 */
export const getGrowthRate = (start: number, latest: number): string => {
  if (start === 0) return '0.0';
  return ((latest - start) / start * 100).toFixed(1);
};

/**
 * 馬のデータから表示用の価格を取得する
 * @param horse 馬のデータ
 * @returns フォーマットされた価格文字列
 */
export const getDisplayPrice = (horse: any): string => {
  if (!horse) return '-';
  
  // 主取りフラグをチェック
  if (isUnsoldHorse(horse)) {
    return '主取り';
  }
  
  // 落札価格がある場合はそれを表示
  if (horse.sold_price !== undefined && horse.sold_price !== null) {
    const formattedPrice = formatPrice(horse.sold_price);
    if (formattedPrice !== '-') {
      return formattedPrice;
    }
  }
  
  // オークション履歴から最新の価格を取得
  if (horse.auction_histories && horse.auction_histories.length > 0) {
    const latestHistory = horse.auction_histories[0];
    if (latestHistory.sold_price !== undefined && latestHistory.sold_price !== null) {
      const formattedPrice = formatPrice(latestHistory.sold_price);
      if (formattedPrice !== '-') {
        return formattedPrice;
      }
    }
  }
  
  return '-';
};
