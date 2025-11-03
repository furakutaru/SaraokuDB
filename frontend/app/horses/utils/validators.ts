import { Horse } from '../types';

/**
 * 馬のデータが有効かどうかを検証する
 * @param horse 検証する馬のデータ
 * @returns 有効な場合はtrue、それ以外はfalse
 */
export const isValidHorse = (horse: Horse): boolean => {
  if (!horse) return false;
  
  // 必須フィールドの検証
  const requiredFields: Array<keyof Horse> = [
    'id', 'name', 'sex', 'age', 'sire', 'dam', 'dam_sire',
    'seller', 'auction_date'
  ];
  
  for (const field of requiredFields) {
    if (horse[field] === undefined || horse[field] === null || horse[field] === '') {
      return false;
    }
  }
  
  // 年齢の検証
  if (typeof horse.age !== 'number' || horse.age < 0 || horse.age > 30) {
    return false;
  }
  
  // 性別の検証
  if (!['牡', '牝', 'セ'].includes(horse.sex)) {
    return false;
  }
  
  return true;
};

/**
 * 価格が有効かどうかを検証する
 * @param price 検証する価格
 * @returns 有効な価格の場合はtrue、それ以外はfalse
 */
export const isValidPrice = (price: any): boolean => {
  if (price === null || price === undefined) return false;
  
  // 数値に変換
  const priceValue = typeof price === 'string' 
    ? parseFloat(price.replace(/[^0-9.-]+/g, '')) 
    : Number(price);
    
  return !isNaN(priceValue) && priceValue > 0;
};

/**
 * 日付が有効な形式かどうかを検証する
 * @param dateString 検証する日付文字列
 * @returns 有効な日付の場合はtrue、それ以外はfalse
 */
export const isValidDate = (dateString: string): boolean => {
  if (!dateString) return false;
  const date = new Date(dateString);
  return !isNaN(date.getTime());
};

/**
 * メールアドレスが有効かどうかを検証する
 * @param email 検証するメールアドレス
 * @returns 有効なメールアドレスの場合はtrue、それ以外はfalse
 */
export const isValidEmail = (email: string): boolean => {
  if (!email) return false;
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
};
