/**
 * 日付をパースするユーティリティ関数
 * @param date パース対象の日付文字列または文字列配列
 * @returns パースされたDateオブジェクト、またはパースできない場合は現在の日付
 */
export const parseDate = (date: string | string[] | undefined): Date => {
  try {
    if (!date) return new Date(0);
    const dateStr = Array.isArray(date) ? date[0] : date;
    if (!dateStr) return new Date(0);
    return new Date(dateStr);
  } catch (error) {
    console.error('日付のパースに失敗しました:', { date, error });
    return new Date(0);
  }
};

/**
 * オークション日付をパースするユーティリティ関数
 * @param dateString パース対象の日付文字列または文字列配列
 * @returns パースされたDateオブジェクト、またはパースできない場合はnull
 */
export const parseAuctionDate = (dateString: string | string[] | null): Date | null => {
  if (!dateString) return null;
  try {
    // 配列形式の文字列をパース
    const dateArray = typeof dateString === 'string' 
      ? JSON.parse(dateString)
      : dateString;
    return dateArray && dateArray[0] ? new Date(dateArray[0]) : null;
  } catch (error) {
    console.error('日付のパースに失敗しました:', error);
    return null;
  }
};

/**
 * 日付をフォーマットする関数
 * @param date フォーマット対象のDateオブジェクト
 * @param formatStr フォーマット文字列（デフォルト: 'yyyy/MM/dd'）
 * @returns フォーマットされた日付文字列
 */
export const formatDate = (date: Date | null, formatStr: string = 'yyyy/MM/dd'): string => {
  if (!date) return '日付不明';
  try {
    const { format } = require('date-fns');
    const { ja } = require('date-fns/locale');
    return format(date, formatStr, { locale: ja });
  } catch (error) {
    console.error('日付のフォーマットに失敗しました:', error);
    return '日付エラー';
  }
};
