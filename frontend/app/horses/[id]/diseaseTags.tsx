import React, { ReactElement } from 'react';

/**
 * 疾病タグをレンダリングするためのユーティリティ関数
 * @param tags 表示するタグ（文字列または文字列の配列）
 * @param className 追加のCSSクラス（オプション）
 * @returns レンダリングされたタグ要素
 */
export function renderDiseaseTags(tags: string | string[] | undefined, className: string = ''): ReactElement | null {
  if (!tags) return null;
  
  const tagList = Array.isArray(tags) ? tags : [tags];
  if (tagList.length === 0) return null;
  
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {tagList.map((tag, index) => (
        <span 
          key={index} 
          className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800"
        >
          {tag}
        </span>
      ))}
    </div>
  );
}

/**
 * コメントから疾病タグを抽出する関数
 * @param comment 抽出元のコメント
 * @param existingTags 既存のタグ（オプション）
 * @returns 抽出された疾病タグの配列
 */
export function extractDiseaseTags(comment: string | null | undefined, existingTags: string[] = []): string[] {
  if (!comment) return [];
  
  // 疾病に関連するキーワード（必要に応じて追加可能）
  const DISEASE_KEYWORDS = [
    '屈腱炎', '骨折', '腫れ', '熱感', '骨瘤', 'ソエ', 
    '管骨瘤', '飛節炎', '球節炎', '靭帯炎', '骨膜炎',
    '跛行', '跛る', '腫脹', '炎症', '裂離', '亀裂',
    '変形', '捻挫', '脱臼', '断裂', '損傷',
    '関節炎', '腱鞘炎', '筋肉痛', '肉離れ', '神経痛'
  ];

  // 既存のタグをセットに追加
  const foundTags = new Set([...existingTags]);

  // コメントからキーワードを検索
  DISEASE_KEYWORDS.forEach(keyword => {
    if (comment.includes(keyword)) {
      foundTags.add(keyword);
    }
  });

  return Array.from(foundTags);
}

/**
 * 疾病タグをレンダリングするためのコンポーネント
 */
interface DiseaseTagsProps {
  tags: string | string[] | undefined;
  className?: string;
}


export const DiseaseTags: React.FC<DiseaseTagsProps> = ({
  tags,
  className = ''
}): ReactElement | null => {
  if (!tags) return null;
  
  const tagList = Array.isArray(tags) ? tags : [tags];
  
  if (tagList.length === 0) return null;
  
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {tagList.map((tag: string, index: number) => (
        <span 
          key={index} 
          className="px-2 py-1 text-xs font-medium rounded-full bg-red-100 text-red-800"
        >
          {tag}
        </span>
      ))}
    </div>
  );
};
