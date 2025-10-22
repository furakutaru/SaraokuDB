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

// 円単位の賞金をフォーマットする（例: 175000 → "17.5万円"）
export function formatPrizeMan(
  val: number | string | null | undefined,
  isUnsold?: boolean
): string {
  // 未落札の場合は「主取り」と表示
  if (isUnsold) {
    return '主取り';
  }

  // 数値に変換
  const num = Number(val);
  
  // 数値に変換できない、または数値が 0 の場合は '-' を返す
  if (isNaN(num) || num === 0) return '-';
  
  // 数値を「○万円」形式にフォーマットして返す
  if (num < 10000) return `${num.toLocaleString('ja-JP')}円`;
  return `${(num / 10000).toFixed(1).replace(/\.0$/, '')}万円`; // 例: 17.0万円 → 17万円
}

// 賞金をフォーマットするヘルパー関数（「17.5万円」形式で表示）
export function formatPrize(value: number | string | null | undefined, raceRecord?: any): string {
  // デバッグ用のログを追加
  console.log('formatPrize - value:', value, 'raceRecord:', raceRecord);
  
  // レース成績が「データなし」または空のオブジェクト、またはレース成績がない場合は「未出走」を返す
  if (raceRecord === undefined || 
      raceRecord === null || 
      raceRecord === 'データなし' || 
      (raceRecord && typeof raceRecord === 'object' && Object.keys(raceRecord).length === 0) ||
      (raceRecord && typeof raceRecord === 'object' && raceRecord.formatted_record === 'データなし') ||
      (raceRecord && typeof raceRecord === 'object' && raceRecord.total_races === 0) ||
      (raceRecord && typeof raceRecord === 'object' && 
       !('total_races' in raceRecord) && 
       !('formatted_record' in raceRecord) && 
       !('wins' in raceRecord))) {
    console.log('formatPrize - 未出走と判定');
    return '未出走';
  }
  
  if (value === null || value === undefined || value === '') return '-';
  
  // 数値に変換
  const numValue = typeof value === 'string' ? parseFloat(value.replace(/[^0-9.-]+/g, '')) : Number(value);
  
  if (isNaN(numValue) || numValue <= 0) return '-';
  
  // 1万円未満の場合はそのまま表示
  if (numValue < 10000) {
    return `${numValue.toLocaleString('ja-JP')}円`;
  }
  
  // 1万円以上の場合は「X.XX万円」形式で表示
  const manValue = numValue / 10000;
  // 小数点以下1桁まで表示（例: 17.5万円）
  const formattedValue = manValue % 1 === 0 ? manValue.toFixed(0) : manValue.toFixed(1);
  return `${formattedValue}万円`;
}

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
export function formatRaceRecord(record: string | null | undefined): string {
  if (!record) return '未出走';
  
  // Unicodeエスケープシーケンスをデコード
  let decoded = record;
  try {
    // Unicodeエスケープシーケンスをデコード
    decoded = record.replace(/\\u([\dA-Fa-f]{4})/g, (_, p1) => {
      return String.fromCharCode(parseInt(p1, 16));
    });
  } catch (e) {
    console.error('Failed to decode race record:', e);
    return record; // デコードに失敗した場合は元の文字列を返す
  }
  
  // 既に正しく表示されている場合はそのまま返す
  if (decoded.includes('戦') || decoded === '未出走') {
    return decoded;
  }
  
  // 形式が「数字 戦 数字 勝」のパターンにマッチするか確認
  const match = decoded.match(/(\d+)\s*[^\d]*\s*(\d+)\s*[^\d]*\s*\[(.*?)\]/);
  if (match) {
    const [, total, wins, details] = match;
    // 引用符を削除して返す
    return `${total}戦${wins}勝[${details}]`;
  }
  
  // マッチしない場合は元の文字列を返す
  return decoded;
}
