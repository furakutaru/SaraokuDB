/**
 * 性別を正規化するヘルパー関数
 * @param sex 性別（文字列、文字列配列、null、undefined）
 * @returns 正規化された性別（'牡'、'牝'、'セ'、'セン' または '不明'）
 */
export const normalizeSex = (sex: string | string[] | null | undefined): string => {
  if (!sex) return '不明';
  
  // 性別のマッピング
  const sexMap: Record<string, string> = {
    '牡': '牡',
    '牝': '牝',
    'セ': 'セ',
    'セン': 'セン',
    // 互換性のためのマッピング
    '牡馬': '牡',
    '牝馬': '牝',
    'セニ': 'セ',
    'filly': '牝',
    'colt': '牡',
    'mare': '牝',
    'horse': '牡',
    'gelding': 'セ',
    'stallion': 'セン',
    'male': '牡',
    'female': '牝',
    '7261': '牡',  // '牡' の Unicode コードポイント
    '725d': '牝',  // '牝' の Unicode コードポイント
    '30bb': 'セ',  // 'セ' の Unicode コードポイント
    '30bb30f3': 'セン'  // 'セン' の Unicode コードポイント
  };

  // 性別の処理
  let sexValue: string | string[] = '';
  
  // 1. 入力値の前処理
  if (typeof sex === 'string') {
    // 文字列の前処理
    let processedSex = sex.trim();
    
    // Unicodeエスケープシーケンスのデコード（\\u725d のような形式）
    if (processedSex.includes('\\u')) {
      processedSex = processedSex.replace(/\\\\u([0-9a-fA-F]{4})/g, (match, p1) => {
        return String.fromCharCode(parseInt(p1, 16));
      });
    }
    
    // JSON配列の可能性がある場合
    if (processedSex.startsWith('[') && processedSex.endsWith(']')) {
      try {
        const parsed = JSON.parse(processedSex);
        if (Array.isArray(parsed) && parsed.length > 0) {
          // 配列の最初の要素を使用
          sexValue = parsed[0];
        }
      } catch (e) {
        console.warn('Failed to parse sex as JSON, using as is:', processedSex);
        sexValue = processedSex;
      }
    } else {
      sexValue = processedSex;
    }
  } 
  // 配列の場合は最初の要素を使用
  else if (Array.isArray(sex)) {
    // 配列の最初の要素を取得（nullやundefinedでない最初の要素）
    const firstValid = sex.find(s => s !== null && s !== undefined);
    if (firstValid !== undefined) {
      sexValue = firstValid;
    }
  }
  
  // 2. 性別の正規化
  if (typeof sexValue === 'string') {
    // 不要な文字を削除
    const cleanedSex = sexValue
      .replace(/[\[\]"\\]/g, '') // 角括弧、引用符、バックスラッシュを削除
      .trim();
    
    // マッピングに存在する場合は変換、それ以外はそのまま表示
    const lowercased = cleanedSex.toLowerCase();
    const result = sexMap[lowercased] || cleanedSex || '不明';
    
    // 空文字列の場合は不明に設定
    return result === '' ? '不明' : result;
  }
  
  return '不明';
};

/**
 * 性別と年齢を適切に表示するためのヘルパー関数
 * @param sex 性別（文字列、文字列配列、null、undefined）
 * @param age 年齢（数値、文字列、null、undefined）
 * @returns フォーマットされた性別と年齢の文字列
 * @deprecated 新しい SexBadge コンポーネントの使用を検討してください
 */
export const formatAge = (sex: string | string[] | null | undefined, age: number | string | null | undefined): string => {
  try {
    // デバッグ用に値をログに出力
    console.log('formatAge - raw input:', { sex, age, typeOfSex: typeof sex, typeOfAge: typeof age });
    
    // 性別と年齢の両方がない場合はハイフンを返す
    if ((!sex || (Array.isArray(sex) && sex.length === 0)) && (age === undefined || age === null || age === '')) {
      return '-';
    }
    
    // 性別を正規化
    const sexText = normalizeSex(sex);
    
    // 3. 年齢の処理
    let ageText = '';
    if (age !== undefined && age !== null && age !== '') {
      const ageNum = Number(age);
      if (!isNaN(ageNum)) {
        ageText = `${ageNum}歳`;
      } else if (typeof age === 'string') {
        // 数値に変換できないが空でない文字列の場合はそのまま表示（不要な文字は削除）
        const cleanedAge = age.trim();
        if (cleanedAge) {
          ageText = cleanedAge;
        }
      }
    }
    
    // 4. 結果を結合して返す（両方ある場合はスペースで区切る）
    const result = [sexText, ageText].filter(Boolean).join(' ');
    console.log('formatAge - result:', { sexText, ageText, result });
    
    return result || '-';
    
  } catch (error) {
    console.error('Error in formatAge:', error, { sex, age });
    // エラーが発生した場合は年齢だけでも返す
    if (age !== undefined && age !== null && age !== '') {
      return `${age}歳`;
    }
    return '-';
  }
};
