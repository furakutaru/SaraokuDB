/**
 * 数値の平均を計算する関数
 * @param numbers - 数値の配列
 * @returns 平均値（配列が空の場合は0）
 */
export function calculateAverage(numbers: number[]): number {
  if (!numbers.length) return 0;
  const sum = numbers.reduce((a, b) => a + b, 0);
  return sum / numbers.length;
}

/**
 * 成長率の平均を計算する関数
 * @param rates - 成長率の配列（%）
 * @returns 平均成長率（%）
 */
export function calculateAverageGrowthRate(rates: number[]): number {
  if (!rates.length) return 0;
  const sum = rates.reduce((a, b) => a + b, 0);
  return sum / rates.length;
}
