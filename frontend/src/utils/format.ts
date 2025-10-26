// Common formatting utilities (no-UI-change)
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

export function formatWeight(weight: number | string | null | undefined): string {
  if (weight === null || weight === undefined || weight === '') return '-';
  // 文字列の場合は数値に変換（カンマや余分な文字を削除）
  const num = typeof weight === 'string' ? parseFloat(weight.toString().replace(/[^0-9.]/g, '')) : Number(weight);
  if (!Number.isFinite(num) || num <= 0) return '-';
  // 数値が整数の場合は小数点以下を表示しない
  const formatted = Number.isInteger(num) ? num.toString() : num.toFixed(1);
  return `${formatted}kg`;
}

// 日付フォーマット用のヘルパー関数
export function formatDate(dateString: string): string {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return format(date, 'yyyy/MM/dd', { locale: ja });
  } catch (e) {
    console.error('日付のフォーマットに失敗しました:', e);
    return dateString;
  }
}

// 配列に変換するユーティリティ
export function toArray<T>(val: T | T[] | undefined | null): T[] {
  if (val === null || val === undefined) return [];
  return Array.isArray(val) ? val : [val];
}

// 成長率を計算する関数
export function calculateGrowthRate(start: number, latest: number): string {
  if (start === 0) return '-';
  const rate = ((latest - start) / start * 100).toFixed(1);
  return (latest - start >= 0 ? '+' : '') + rate;
}

// 数値を「○万円」または「〇円」形式の文字列に変換する関数
export function formatManYen(value: number): string {
  if (value === 0) return '0円';
  if (!value) return '-';
  if (value < 10000) return `${value}円`;
  const manYen = (value / 10000).toFixed(1);
  return `${manYen}万円`;
}

// 数値を3桁区切りでフォーマットする
function formatNumberWithCommas(num: number): string {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * 落札価格をフォーマットする
 * @param price 価格（数値または文字列）
 * @param isUnsold 未落札フラグ
 * @param unsoldFlag 未落札フラグ（互換性のため）
 * @param soldPrice 実際の売却価格（price の代わりに使用）
 * @param unsoldCount 未落札回数
 * @returns フォーマットされた価格文字列（例: "¥1,000,000" または "主取り"）
 */
// セラー名をフォーマット
export function formatSeller(seller: string | string[] | null): string {
  if (!seller) return '-';
  
  try {
    // JSON文字列の場合はパース
    const parsed = typeof seller === 'string' && seller.startsWith('[') 
      ? JSON.parse(seller) 
      : seller;
    return Array.isArray(parsed) && parsed.length > 0 ? parsed[0] : '-';
  } catch {
    return '-';
  }
}

export function formatPrice(
  price: number | string | null | undefined,
  isUnsold: boolean = false,
  unsoldFlag?: boolean,
  soldPrice?: number | string | null | undefined,
  unsoldCount: number = 0
): string {
  // 主取りフラグが立っている場合、またはunsold_countが1以上の場合は「主取り」を返す
  if (isUnsold === true || unsoldFlag === true || unsoldCount > 0) {
    return '主取り';
  }
  
  // soldPrice を優先し、なければ price を使用
  let effectivePrice = soldPrice !== undefined ? soldPrice : price;
  
  // 価格が null または undefined または空文字の場合は「-」を返す
  if (effectivePrice === null || effectivePrice === undefined || effectivePrice === '') {
    return '-';
  }
  
  // 文字列で [ で始まる場合は JSON 配列とみなしてパースを試みる
  if (typeof effectivePrice === 'string' && effectivePrice.startsWith('[')) {
    try {
      const parsedArray = JSON.parse(effectivePrice);
      if (Array.isArray(parsedArray) && parsedArray.length > 0) {
        effectivePrice = parsedArray[0]; // 最初の要素を使用
      }
    } catch (e) {
      console.error('価格のパースに失敗しました:', e);
    }
  }
  
  // 数値に変換（文字列の場合は数字とドット、マイナス以外を除去）
  let num: number;
  if (typeof effectivePrice === 'string') {
    const parsed = parseFloat(effectivePrice.replace(/[^0-9.-]+/g, ''));
    num = isNaN(parsed) ? 0 : parsed;
  } else if (typeof effectivePrice === 'number') {
    num = effectivePrice;
  } else {
    return '-';
  }
  
  // 数値が無効または0以下の場合は「-」を返す
  if (num <= 0) {
    return '-';
  }
  
  // 3桁区切りでフォーマット
  return `¥${num.toLocaleString('ja-JP')}`;
}

/**
 * 賞金をフォーマットする（未出走チェックなし）
 * @param amount 賞金額（数値または文字列）
 * @returns フォーマットされた賞金文字列（例: "1,000万円" または "500円"）
 */
export function formatPrize(amount: number | string | null | undefined): string {
  // 値がnullまたはundefinedまたは空文字の場合は'-'を返す
  if (amount === null || amount === undefined || amount === '') {
    return '-';
  }
  
  // 数値に変換
  const numAmount = Number(amount);
  
  // 数値に変換できない、または0の場合は'0円'を返す
  if (isNaN(numAmount) || numAmount === 0) {
    return '0円';
  }
  
  // 1万円未満は円単位で表示
  if (numAmount < 10000) {
    return `${numAmount.toLocaleString('ja-JP')}円`;
  }
  
  // 1万円以上の場合は「○万円」形式で表示
  const manYen = numAmount / 10000;
  // 小数点以下1桁まで表示（例: 17.5万円）
  const formattedValue = manYen % 1 === 0 ? manYen.toFixed(0) : manYen.toFixed(1);
  return `${formattedValue}万円`;
}

/**
 * 賞金をフォーマットする（未出走チェックあり）
 * @param amount 賞金額（数値または文字列）
 * @param raceRecordInfo レース記録情報（未出走判定用）
 * @returns フォーマットされた賞金文字列（例: "1,000万円" または "未出走"）
 */
export function formatPrizeWithRaceCheck(
  amount: number | string | null | undefined,
  raceRecordInfo?: any
): string {
  // 未出走チェック
  const isUnraced = (record: any): boolean => {
    if (record === null || record === undefined || record === '') {
      return false;
    }
    
    if (Array.isArray(record)) {
      return record.length === 0 || isUnraced(record[0]);
    }
    
    if (typeof record === 'string') {
      return record === 'データなし' || record === '未出走' || record === '';
    }
    
    if (typeof record === 'object') {
      if (Object.keys(record).length === 0) return false;
      
      if ('is_unraced' in record && record.is_unraced === true) return true;
      if ('total_races' in record) {
        const totalRaces = record.total_races;
        return totalRaces === 0 || totalRaces === '0' || totalRaces === '0戦0勝';
      }
      if ('formatted_record' in record) {
        const formattedRecord = record.formatted_record;
        return formattedRecord === 'データなし' || formattedRecord === '未出走';
      }
      if ('race_records' in record) {
        const raceRecords = record.race_records;
        return Array.isArray(raceRecords) && raceRecords.length === 0;
      }
      
      const unracedIndicators = ['unraced', '未出走', 'データなし', 'no_data', 'nodata'];
      return Object.values(record).some(value => 
        unracedIndicators.includes(String(value).toLowerCase())
      );
    }
    
    return false;
  };

  // 未出走の場合は「未出走」を返す
  if (raceRecordInfo && isUnraced(raceRecordInfo)) {
    return '未出走';
  }
  
  // 未出走でない場合は通常の賞金フォーマットを返す
  return formatPrize(amount);
}

// 後方互換性のため、古い関数名をエクスポート
// 新しいコードでは formatPrize または formatPrizeWithRaceCheck を使用してください
export const formatPrizeMan = formatPrizeWithRaceCheck;

// 円単位の数値を「○万円」形式に変換する
// 例: 175000 → "17.5万円"
export function formatPrizeFromYen(val: number | string | string[] | { total_prize: string } | null | undefined): string {
  if (val === null || val === undefined || val === '') return '-';
  
  let num: number;
  
  if (typeof val === 'number') {
    num = val;
  } else if (Array.isArray(val)) {
    // 配列の場合は最初の要素を数値に変換
    const firstVal = val[0];
    if (firstVal === undefined) return '-';
    num = Number(String(firstVal).replace(/[^0-9.-]/g, ''));
  } else if (typeof val === 'string') {
    // 文字列が配列形式（例: "[380000]"）の場合はパースしてから処理
    if (val.startsWith('[') && val.endsWith(']')) {
      try {
        const parsedArray = JSON.parse(val);
        if (Array.isArray(parsedArray) && parsedArray.length > 0) {
          const firstVal = parsedArray[0];
          num = Number(String(firstVal).replace(/[^0-9.-]/g, ''));
        } else {
          return '0万円';
        }
      } catch (e) {
        console.error('Error parsing array string:', e);
        return '0万円';
      }
    } else {
      // 通常の文字列の場合は数値に変換
      num = Number(val.replace(/[^0-9.-]/g, ''));
    }
  } else if (typeof val === 'object' && val !== null && 'total_prize' in val) {
    num = Number(String(val.total_prize).replace(/[^0-9.-]/g, ''));
  } else {
    return '0万円';
  }
  
  if (isNaN(num) || num === 0) return '0万円';
  if (num < 10000) return `${num}円`;
  return `${(num / 10000).toFixed(1)}万円`;
}

// 通貨をフォーマットする（例: 1820000 → "¥1,820,000"）
export function formatCurrency(value: number | string | null | undefined): string {
  if (value === null || value === undefined || value === '') return '-';
  const numValue = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(numValue) || numValue <= 0) return '-';
  
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    maximumFractionDigits: 0
  }).format(numValue);
}

// 戦績をフォーマットする
// 例: "6\u62260\u52dd[0-0-0-6]" → "6戦0勝 [0-0-0-6]"
export function formatRaceRecord(record: any): string {
  // 文字列で「未出走」が指定されている場合
  if (typeof record === 'string' && record === '未出走') {
    return '未出走';
  }
  
  // null または undefined の場合
  if (!record) return '未出走';
  
  // オブジェクトで total_races が 0 または存在しない場合
  if (typeof record === 'object') {
    if (Object.keys(record).length === 0) {
      return '未出走';
    }
    
    if (record.total_races === 0 || record.total_races === '0' || 
        record.total_races === undefined || record.total_races === null) {
      return '未出走';
    }
    
    // フォーマット済みのレコードがある場合はそれを返す
    if (record.formatted_record) {
      return record.formatted_record;
    }
    
    // シンプルなフォーマット
    if (record.record_format === 'simple' && record.total_races !== undefined) {
      return `${record.total_races}戦${record.wins || 0}勝`;
    }
    
    // 詳細なフォーマット
    if (record.record_format === 'detailed') {
      const { first, second, third, fourth } = record;
      return `${first}-${second}-${third}-${fourth}`;
    }
  }
  
  // 文字列で [ が含まれる場合の処理（従来のフォーマット）
  if (typeof record === 'string') {
    const match = record.match(/(\d+)戦(\d+)勝\[(\d+)-(\d+)-(\d+)-(\d+)\]/);
    if (match) {
      const [_, total, wins, first, second, third, fourth] = match;
      return `${total}戦${wins}勝 [${first}-${second}-${third}-${fourth}]`;
    }
    
    // 戦績が空の場合は未出走と表示
    if (record === '' || record === 'データなし') {
      return '未出走';
    }
    
    // その他の文字列はそのまま返す
    return record;
  }
  
  // 上記のいずれにも該当しない場合は未出走を返す
  return '未出走';
}
