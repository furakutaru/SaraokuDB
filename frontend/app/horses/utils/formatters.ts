import { Horse } from '../types';

// Horse型を拡張してunsoldプロパティを追加
declare module '../types' {
  interface Horse {
    unsold?: boolean;
    is_unsold?: boolean;
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
export const formatPrice = (price: number | string | null | undefined): string => {
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

/**
 * 売り主情報を適切に表示するためのヘルパー関数
 * @param seller 売り主情報
 * @returns フォーマットされた売り主情報
 */
export const formatSeller = (seller: string | null | undefined): string => {
  if (!seller) return '-';
  // インヴイス登録情報を削除
  return seller.replace(/\(.*\)/g, '').trim();
};

/**
 * 賞金を表示用にフォーマットする関数
 * @param val 賞金の値
 * @returns フォーマットされた賞金文字列
 */
export const formatPrize = (val: number | string | null | undefined): string => {
  if (val === null || val === undefined || val === '') return '-';
  
  const num = typeof val === 'string' ? parseFloat(val) : val;
  return isNaN(num) ? '-' : num.toLocaleString('ja-JP') + '万円';
};

/**
 * 成長率を計算する関数
 * @param start 開始値
 * @param latest 最新値
 * @returns 成長率（パーセント）の文字列表現
 */
export const getGrowthRate = (start: number, latest: number): string => {
  if (start <= 0) return latest > 0 ? '∞' : '0.0%';
  const rate = ((latest - start) / start) * 100;
  return rate.toFixed(1) + '%';
};

/**
 * 馬のデータから表示用の価格を取得する
 * @param horse 馬のデータ
 * @returns フォーマットされた価格文字列
 */
export const getDisplayPrice = (horse: Horse): string => {
  if (!horse) return '-';
  
  // 1. 主取りチェック
  if (isUnsoldHorse(horse)) {
    return '主取り';
  }

  // 2. sold_price が存在する場合
  if (horse.sold_price !== null && horse.sold_price !== undefined) {
    return formatPrice(horse.sold_price);
  }

  // 3. 履歴から最新の価格を取得
  if (horse.auction_histories && horse.auction_histories.length > 0) {
    // 日付でソート（新しい順）
    const sortedHistory = [...horse.auction_histories].sort((a, b) => {
      // auction_date が配列の場合は最初の要素を使用
      const dateAStr = Array.isArray(a.auction_date) ? a.auction_date[0] : a.auction_date;
      const dateBStr = Array.isArray(b.auction_date) ? b.auction_date[0] : b.auction_date;
      
      const dateA = dateAStr ? new Date(dateAStr).getTime() : 0;
      const dateB = dateBStr ? new Date(dateBStr).getTime() : 0;
      return dateB - dateA;
    });

    // 最新の有効な価格を探す
    const latestPrice = sortedHistory.find(item => 
      item.sold_price !== null && item.sold_price !== undefined
    )?.sold_price;

    if (latestPrice) {
      return formatPrice(latestPrice);
    }
  }

  // 4. 価格情報が見つからない場合
  return '-';
};
