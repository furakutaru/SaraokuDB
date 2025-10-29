/**
 * 性別に基づいて色を返すユーティリティ関数
 */

type SexColorMap = {
  [key: string]: string;
};

const sexColorMap: SexColorMap = {
  '牡': 'bg-blue-500',
  '牡馬': 'bg-blue-500',
  'M': 'bg-blue-500',
  'male': 'bg-blue-500',
  '牝': 'bg-pink-500',
  '牝馬': 'bg-pink-500',
  'F': 'bg-pink-500',
  'female': 'bg-pink-500',
  'セ': 'bg-purple-500',
  'セネ': 'bg-purple-500',
  'G': 'bg-purple-500',
  'gelding': 'bg-purple-500',
  '去勢': 'bg-purple-500',
  '去勢馬': 'bg-purple-500',
  'その他': 'bg-gray-500',
  '不明': 'bg-gray-400',
  '': 'bg-gray-400',
};

/**
 * 性別に基づいて背景色のクラスを返す
 * @param sex 性別（'牡', '牝', 'セ' など）
 * @returns 対応するTailwind CSSの背景色クラス
 */
export const getSexColor = (sex: string | null | undefined): string => {
  if (!sex) return 'bg-gray-400';
  
  // 性別を正規化（前後の空白を削除）
  const normalizedSex = sex.trim();
  
  // マップに存在する場合はその値を、ない場合はデフォルトの色を返す
  return sexColorMap[normalizedSex] || 'bg-gray-400';
};

/**
 * 性別を短縮形に変換する
 * @param sex 性別
 * @returns 短縮形の性別（'牡', '牝', 'セ' のいずれか）
 */
export const formatSex = (sex: string | null | undefined): string => {
  if (!sex) return '';
  
  const normalizedSex = sex.trim();
  const sexMap: { [key: string]: string } = {
    '牡': '牡',
    '牡馬': '牡',
    'M': '牡',
    'male': '牡',
    '牝': '牝',
    '牝馬': '牝',
    'F': '牝',
    'female': '牝',
    'セ': 'セ',
    'セネ': 'セ',
    'G': 'セ',
    'gelding': 'セ',
    '去勢': 'セ',
    '去勢馬': 'セ',
  };
  
  return sexMap[normalizedSex] || normalizedSex;
};
