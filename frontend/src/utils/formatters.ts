/**
 * 馬体重をフォーマットする関数
 * @param weight - 体重（数値または文字列）
 * @returns フォーマットされた体重文字列（例: "450kg"）
 */
export function formatWeight(weight: number | string | null | undefined): string {
  console.log('formatWeight called with:', weight, 'type:', typeof weight);
  if (weight === null || weight === undefined || weight === '') {
    return '-';
  }
  const num = typeof weight === 'string' ? parseInt(weight, 10) : Math.floor(Number(weight));
  return isNaN(num) ? '-' : `${num}kg`;
}

/**
 * ROIを計算する関数
 * @param prize - 賞金（数値、文字列、または { total_prize: string } オブジェクト）
 * @param price - 価格（数値または文字列）
 * @returns フォーマットされたROI文字列（例: "150.5%"）
 */
export function calcROI(
  prize: number | string | { total_prize: string } | undefined,
  price: number | string | undefined
): string {
  // 賞金を数値に変換
  let prizeNum = 0;
  if (prize !== undefined && prize !== null) {
    if (typeof prize === 'object' && 'total_prize' in prize) {
      prizeNum = parseFloat(prize.total_prize.replace(/,/g, '')) || 0;
    } else if (typeof prize === 'string') {
      prizeNum = parseFloat(prize.replace(/,/g, '')) || 0;
    } else if (typeof prize === 'number') {
      prizeNum = prize;
    }
  }

  // 価格を数値に変換
  const numPrice = typeof price === 'string' ? parseFloat(price.replace(/,/g, '')) : price || 0;
  
  // ROIを計算（賞金 / 価格）
  if (isNaN(prizeNum) || isNaN(numPrice) || numPrice === 0) return '-';
  
  const roi = (prizeNum / numPrice) * 100; // パーセント表示
  return roi.toFixed(1) + '%';
}

// 既存のフォーマット関数を再エクスポート
export { formatPrice, getDisplayPrice } from './price';
