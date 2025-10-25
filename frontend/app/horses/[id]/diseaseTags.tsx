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
 * バックエンドから疾病タグを取得する関数
 * @param comment 抽出元のコメント
 * @param existingTags 既存のタグ（オプション）
 * @returns 抽出された疾病タグの配列
 */
export async function extractDiseaseTags(comment: string | null | undefined, existingTags: string[] = []): Promise<string[]> {
  if (!comment) return [];
  
  try {
    // バックエンドAPIを呼び出して疾病タグを取得
    const response = await fetch('/api/extract-disease-tags', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ comment }),
    });

    if (!response.ok) {
      throw new Error('疾病タグの取得に失敗しました');
    }

    const data = await response.json();
    const extractedTags = data.tags || [];
    
    // 既存のタグと抽出されたタグをマージして重複を削除
    return Array.from(new Set([...existingTags, ...extractedTags]));
  } catch (error) {
    console.error('Error fetching disease tags:', error);
    // エラーが発生した場合は既存のタグをそのまま返す
    return [...existingTags];
  }
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
