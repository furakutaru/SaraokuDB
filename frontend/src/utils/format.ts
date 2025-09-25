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
