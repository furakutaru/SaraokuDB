/**
 * コメントから病歴タグを抽出する関数
 * @param comment 抽出元のコメント
 * @returns 抽出されたタグの配列
 */
export const extractDiseaseTags = (comment: string | null | undefined): string[] => {
  if (!comment) return [];
  
  // 病歴タグを抽出する正規表現パターン
  const diseasePatterns = [
    /(?:病歴|既往症)[:：]\s*([^\n。、,]+)/g,  // 「病歴: 〇〇」や「既往症：〇〇」の形式
    /(?:病歴|既往症)[^\n。、,]+/g,      // 「病歴あり」や「既往症あり」などの単純なマッチ
  ];
  
  const tags = new Set<string>();
  
  // 各パターンでマッチングを試みる
  for (const pattern of diseasePatterns) {
    let match;
    while ((match = pattern.exec(comment)) !== null) {
      if (match[1]) {
        // キャプチャグループがある場合（1番目のパターン）
        const tag = match[1].trim();
        if (tag && tag !== 'なし' && tag !== '無し' && tag !== '無') {
          tags.add(tag);
        }
      } else if (match[0]) {
        // キャプチャグループがない場合（2番目のパターン）
        const matchedText = match[0].trim();
        if (matchedText.includes('あり') || matchedText.includes('有り')) {
          tags.add('病歴あり');
        }
      }
    }
  }
  
  return Array.from(tags);
};

export default extractDiseaseTags;
