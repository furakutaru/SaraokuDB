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

// 数値を「○万円」形式の文字列に変換する関数
export function formatManYen(value: number): string {
  if (value === 0) return '0円';
  if (!value) return '-';
  return `${(value / 10000).toFixed(1)}万円`;
}

// 数値を3桁区切りでフォーマットする
function formatNumberWithCommas(num: number): string {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// 円単位の数値をフォーマットする
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
  
  // 数値を3桁区切りでフォーマットして返す
  return `¥${formatNumberWithCommas(Math.round(num))}`;
}

// For values in Yen (number/string/object), display as 万円
export function formatPrizeFromYen(val: number | string | { total_prize: string } | null | undefined): string {
  if (val === null || val === undefined || val === '') return '-';
  if (typeof val === 'number') {
    return val > 0 ? `${(val / 10000).toLocaleString('ja-JP')}万円` : '0万円';
  }
  if (typeof val === 'string') {
    const num = Number(val.replace(/[^0-9]/g, ''));
    return !isNaN(num) && num > 0 ? `${(num / 10000).toLocaleString('ja-JP')}万円` : '0万円';
  }
  if (typeof val === 'object' && val !== null && 'total_prize' in val) {
    const num = Number(String(val.total_prize).replace(/[^0-9]/g, ''));
    return !isNaN(num) && num > 0 ? `${(num / 10000).toLocaleString('ja-JP')}万円` : '0万円';
  }
  return '0万円';
}

/**
 * 戦績をフォーマットする
 * 例: "6\u62260\u52dd[0-0-0-6]" → "6戦0勝 [0-0-0-6]"
 */
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
