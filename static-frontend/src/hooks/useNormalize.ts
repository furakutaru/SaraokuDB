import { useMemo } from 'react';
import { 
  formatDate, 
  formatCurrency, 
  formatPrize, 
  formatSex, 
  formatWeight, 
  parseTags, 
  calculateGrowthRate,
  normalizeImageUrl
} from '@/utils/normalize';

/**
 * 正規化関数を使用するためのカスタムフック
 */
export const useNormalize = () => {
  const normalize = useMemo(() => ({
    // 日付をフォーマット
    formatDate: (dateString: string | Date): string => formatDate(dateString),
    
    // 通貨をフォーマット
    formatCurrency: (value: number | string | null | undefined): string => formatCurrency(value),
    
    // 賞金をフォーマット
    formatPrize: (value: number | string | null | undefined): string => formatPrize(value),
    
    // 性別をフォーマット
    formatSex: (sex: string | null | undefined) => formatSex(sex),
    
    // 体重をフォーマット
    formatWeight: (weight: number | string | null | undefined): string => formatWeight(weight),
    
    // タグをパース
    parseTags: (tags: string | string[] | null | undefined): string[] => parseTags(tags),
    
    // 成長率を計算
    calculateGrowthRate: (start: number, latest: number): string => calculateGrowthRate(start, latest),
    
    // 画像URLを正規化
    normalizeImageUrl: (url: string | null | undefined, fallback?: string): string => 
      normalizeImageUrl(url, fallback),
    
    // 落札価格を表示用にフォーマット
    formatSoldPrice: (price: number | string | null | undefined, isUnsold: boolean = false): string => {
      if (isUnsold) return '主取り';
      if (price === null || price === undefined || price === '') return '-';
      
      const num = typeof price === 'string' ? parseFloat(price.replace(/[^0-9.-]+/g, '')) : price;
      
      if (isNaN(num) || num <= 0) return '-';
      
      return `¥${num.toLocaleString('ja-JP')}`;
    },
    
    // 年齢をフォーマット
    formatAge: (age: number | string | null | undefined): string => {
      if (age === null || age === undefined || age === '') return '-';
      return `${age}歳`;
    },
    
    // 賞金の差分をフォーマット
    formatPrizeDiff: (start: number, latest: number): { value: string; isPositive: boolean } => {
      if (isNaN(start) || isNaN(latest)) {
        return { value: '-', isPositive: false };
      }
      
      const diff = latest - start;
      const isPositive = diff >= 0;
      
      if (diff === 0) {
        return { value: '0万円', isPositive: false };
      }
      
      return {
        value: `${isPositive ? '+' : ''}${formatPrize(diff)}`,
        isPositive
      };
    }
  }), []);

  return normalize;
};

export default useNormalize;
