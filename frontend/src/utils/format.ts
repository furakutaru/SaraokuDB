// Common formatting utilities (no-UI-change)

export function formatWeight(weight: number | string | null | undefined): string {
  if (weight === null || weight === undefined || weight === '') return '-';
  const num = typeof weight === 'string' ? parseFloat(weight.replace(/[^0-9.]/g, '')) : Number(weight);
  if (!Number.isFinite(num) || num <= 0) return '-';
  const formatted = Number.isInteger(num) ? String(num) : num.toFixed(1);
  return `${formatted}kg`;
}

// For values already expressed in "万円" units (e.g., 123.4 means 123.4万円)
export function formatPrizeMan(val: number | string | null | undefined): string {
  if (val === null || val === undefined || val === '' || isNaN(Number(val))) return '-';
  return `${Number(val).toFixed(1)}万円`;
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
