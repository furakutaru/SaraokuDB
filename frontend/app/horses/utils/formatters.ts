import { Horse } from '../types';

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

/**
 * 性別と年齢を適切に表示するためのヘルパー関数
 * @param sex 性別
 * @param age 年齢
 * @returns フォーマットされた性別と年齢の文字列
 */
export const formatAge = (sex: string | string[] | null | undefined, age: number | string | null | undefined): string => {
  // デバッグ用に値をログに出力
  console.log('formatAge - raw sex:', sex, 'age:', age);
  
  // 性別と年齢の両方がない場合はハイフンを返す
  if ((!sex || (Array.isArray(sex) && sex.length === 0)) && (age === undefined || age === null)) {
    return '-';
  }
  
  // 性別のマッピング
  const sexMap: Record<string, string> = {
    '牡': '牡',
    '牝': '牝',
    'セ': 'セ',
    '牡馬': '牡',
    '牝馬': '牝',
    'セニ': 'セ',
    'filly': '牝',
    'colt': '牡',
    'mare': '牝',
    'horse': '牡',
    'gelding': 'セ',
    'male': '牡',
    'female': '牝',
    '7261': '牡',  // '牡' の Unicode コードポイント
    '725d': '牝',  // '牝' の Unicode コードポイント
    '30bb': 'セ'   // 'セ' の Unicode コードポイント
  };

  // 性別の処理
  let sexValue: string | string[] = '';
  
  try {
    // 文字列でJSON配列の可能性がある場合
    if (typeof sex === 'string' && sex.startsWith('[') && sex.endsWith(']')) {
      try {
        // JSON配列としてパースを試みる
        const parsed = JSON.parse(sex);
        if (Array.isArray(parsed) && parsed.length > 0) {
          sexValue = parsed[0];
        }
      } catch (e) {
        console.warn('Failed to parse sex as JSON:', sex);
        sexValue = sex;
      }
    } 
    // 配列の場合は最初の要素を使用
    else if (Array.isArray(sex)) {
      // 配列の最初の要素を取得（nullやundefinedでない最初の要素）
      const firstValid = sex.find(s => s !== null && s !== undefined);
      if (firstValid !== undefined) {
        sexValue = firstValid;
      }
    } 
    // それ以外の場合はそのまま使用
    else if (sex !== undefined && sex !== null) {
      sexValue = sex;
    }
    
    // 文字列の場合は不要な文字を削除して正規化
    if (typeof sexValue === 'string') {
      // Unicodeエスケープシーケンスをデコード
      let decoded = sexValue;
      
      // Unicodeエスケープシーケンスを処理 (\u725d のような形式)
      if (decoded.includes('\\u')) {
        decoded = decoded.replace(/\\u([0-9a-fA-F]{4})/g, (match, p1) => {
          return String.fromCharCode(parseInt(p1, 16));
        });
      }
      
      // 角括弧、引用符、バックスラッシュ、uなどの不要な文字を削除
      decoded = decoded
        .replace(/[\[\]"\\]/g, '') // 角括弧、引用符、バックスラッシュを削除
        .trim();
      
      // 4桁の16進数コードを確認
      const hexMatch = decoded.match(/^([0-9a-fA-F]{4})$/);
      if (hexMatch) {
        const code = hexMatch[1].toLowerCase();
        if (sexMap[code]) {
          return `${sexMap[code]}${age ? ` ${age}歳` : ''}`.trim() || '-';
        }
      }
      
      // マッピングに存在する場合は変換、それ以外はそのまま表示
      sexValue = sexMap[decoded.toLowerCase()] || decoded || '不明';
    } 
    // 数値の場合は文字列に変換
    else if (typeof sexValue === 'number') {
      sexValue = String(sexValue);
    }
    // nullまたはundefinedの場合は不明に設定
    else if (sexValue === null || sexValue === undefined) {
      sexValue = '不明';
    }
    
    // 年齢の処理
    let ageText = '';
    if (age !== undefined && age !== null && age !== '') {
      const ageNum = Number(age);
      if (!isNaN(ageNum)) {
        ageText = `${ageNum}歳`;
      } else if (typeof age === 'string' && age.trim() !== '') {
        // 数値に変換できないが空でない文字列の場合はそのまま表示
        ageText = age;
      }
    }
    
    // 性別と年齢を結合して返す（両方ある場合はスペースで区切る）
    const sexText = Array.isArray(sexValue) ? sexValue[0] || '' : sexValue;
    const result = [sexText, ageText].filter(Boolean).join(' ');
    console.log('formatAge - result:', result);
    return result || '-';
    
  } catch (error) {
    console.error('Error in formatAge:', error, { sex, age });
    return age ? `${age}歳` : '-';
  }
};

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
