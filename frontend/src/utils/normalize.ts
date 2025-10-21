/**
 * 日付をフォーマットする関数
 * @param dateString - 日付文字列
 * @returns フォーマットされた日付文字列 (例: "2023年1月1日")
 */
export const formatDate = (dateString: string | Date): string => {
  if (!dateString) return '-';
  
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }).format(date);
  } catch (e) {
    console.error('日付のフォーマットに失敗しました:', e);
    return String(dateString);
  }
};

/**
 * 数値を通貨形式（円）にフォーマットする関数
 * @param value - 数値
 * @returns フォーマットされた通貨文字列 (例: "1,234,567円")
 */
export const formatCurrency = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === '') return '-';
  
  const num = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value;
  
  if (isNaN(num) || num === 0) return '-';
  
  return new Intl.NumberFormat('ja-JP', {
    style: 'currency',
    currency: 'JPY',
    maximumFractionDigits: 0,
  }).format(num);
};

/**
 * 賞金を万円単位でフォーマットする関数
 * @param value - 万円単位の数値
 * @returns フォーマットされた賞金文字列 (例: "1,234.5万円")
 */
export const formatPrize = (value: number | string | null | undefined): string => {
  if (value === null || value === undefined || value === '') return '-';
  
  const num = typeof value === 'string' ? parseFloat(value.replace(/,/g, '')) : value;
  
  if (isNaN(num)) return '-';
  
  return num === 0 ? '0万円' : `${num.toLocaleString('ja-JP')}万円`;
};

/**
 * 性別を表示用にフォーマットする関数
 * @param sex - 性別文字列 (例: "牡", "牝", "セ")
 * @returns フォーマットされた性別情報
 */
export const formatSex = (sex: string | null | undefined): string => {
  if (!sex) return '-';
  
  // 性別の正規化（前後の空白を削除し、全角に統一）
  const normalizedSex = sex.toString().trim()
    .replace(/[ \t\n\r\f\v]/g, '') // 空白文字を削除
    .replace(/♂/g, '牡')  // ♂ を 牡 に変換
    .replace(/♀/g, '牝')  // ♀ を 牝 に変換
    .replace(/セイ|せい|せん|セン/g, 'セ'); // セイ, せい, せん, セン を セ に変換
  
  // 性別に応じたスタイルを返す
  const sexMap: Record<string, string> = {
    '牡': '牡',
    '牝': '牝',
    'セ': 'セ',
  };
  
  return sexMap[normalizedSex] || normalizedSex || '-';
};

/**
 * 性別に応じた背景色を取得する関数
 * @param sex - 性別文字列 (例: "牡", "牝", "セ")
 * @returns 背景色のクラス名
 */
export const getSexColor = (sex: string | null | undefined): string => {
  if (!sex) return 'bg-gray-200';
  
  const normalizedSex = sex.toString().trim()
    .replace(/[ \t\n\r\f\v]/g, '')
    .replace(/♂/g, '牡')
    .replace(/♀/g, '牝')
    .replace(/セイ|せい|せん|セン/g, 'セ');
  
  const colorMap: Record<string, string> = {
    '牡': 'bg-blue-600',
    '牝': 'bg-pink-500',
    'セ': 'bg-green-600',
  };
  
  return colorMap[normalizedSex] || 'bg-gray-200';
};

/**
 * 体重をフォーマットする関数
 * @param weight - 体重 (kg)
 * @returns フォーマットされた体重文字列 (例: "450kg")
 */
export const formatWeight = (weight: number | string | null | undefined): string => {
  if (weight === null || weight === undefined || weight === '') return '-';
  
  const num = typeof weight === 'string' ? parseFloat(weight) : weight;
  
  if (isNaN(num)) return '-';
  
  return `${num}kg`;
};

/**
 * タグを配列に変換する関数
 * @param tags - タグ文字列 (カンマ区切り)
 * @returns タグの配列
 */
export const parseTags = (tags: string | string[] | null | undefined): string[] => {
  if (!tags) return [];
  
  if (Array.isArray(tags)) {
    return tags.flatMap(tag => 
      String(tag).split(',')
        .map(t => t.trim())
        .filter(Boolean)
    );
  }
  
  return String(tags).split(',')
    .map(tag => tag.trim())
    .filter(Boolean);
};

/**
 * 成長率を計算する関数
 * @param start - 開始時の値
 * @param latest - 最新の値
 * @returns 成長率の文字列 (例: "+10.5%")
 */
export const calculateGrowthRate = (start: number, latest: number): string => {
  if (start === 0 || isNaN(start) || isNaN(latest)) return '-';
  
  const rate = ((latest - start) / start) * 100;
  const formattedRate = Math.abs(rate).toFixed(1);
  
  return `${rate >= 0 ? '+' : '-'}${formattedRate}%`;
};

/**
 * 画像URLを正規化する関数
 * @param url - 画像URL
 * @param fallback - フォールバック画像URL
 * @returns 正規化された画像URL
 */
export const normalizeImageUrl = (url: string | null | undefined, fallback: string = ''): string => {
  if (!url) return fallback;
  
  // URLが相対パスの場合は絶対URLに変換
  if (url.startsWith('/')) {
    return `${process.env.NEXT_PUBLIC_BASE_URL || ''}${url}`;
  }
  
  return url;
};
