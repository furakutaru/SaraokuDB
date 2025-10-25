'use client';

import React from 'react';
import { Card, CardContent, Typography, Button } from '@mui/material';
import { ExtendedAuctionHistory } from '../types';
import { DiseaseTags } from '../diseaseTags';

interface CommentCardProps {
  history: ExtendedAuctionHistory[];
  activeTab: number;
  hasComments: boolean;
  onTabChange: (index: number) => void;
}

export const CommentCard: React.FC<CommentCardProps> = ({
  history,
  activeTab,
  hasComments,
  onTabChange,
}) => {
  // コメントがあるかどうかをチェックするヘルパー関数
  const hasComment = (index: number) => {
    return history[index]?.comment?.trim() !== '';
  };

  // コメントがある履歴の数をカウント
  const commentCount = history.filter(h => h.comment?.trim()).length;
  
  // 1回目のみの場合はタブを表示しない
  const showTabs = commentCount > 1;
  
  // 表示するコメントを決定（タブ表示の場合はアクティブなタブ、そうでない場合は最初のコメント）
  const displayComment = history[activeTab] || history[0];

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        {/* タブ表示（コメントが2つ以上ある場合のみ表示） */}
        {showTabs && (
          <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
            {history.map((h, i) => {
              const hasComment = h.comment?.trim() !== '';
              return (
                <button
                  key={i}
                  className={`px-3 py-1 rounded whitespace-nowrap ${
                    activeTab === i 
                      ? 'bg-blue-600 text-white' 
                      : hasComment 
                        ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' 
                        : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                  }`}
                  onClick={() => onTabChange(i)}
                  disabled={!hasComment}
                >
                  {i + 1}回目 {!hasComment && '(コメントなし)'}
                </button>
              );
            })}
          </div>
        )}
        
        <div className="border p-4 bg-gray-50 rounded min-h-[100px]">
          {hasComments && displayComment ? (
            displayComment.comment?.trim() ? (
              <div className="prose max-w-none">
                <p className="whitespace-pre-line text-gray-800">
                  {displayComment.comment 
                    ? displayComment.comment
                        // Remove square brackets and quotes at the beginning and end
                        .replace(/^\s*[\[\]"]+|[\]"\s]+$/g, '')
                        // Decode Unicode escape sequences
                        .replace(/\\u([\dA-Fa-f]{4})/g, (match: string, grp: string) => 
                          String.fromCharCode(parseInt(grp, 16))
                        )
                        // Replace escaped newlines with actual newlines
                        .replace(/\\n/g, '\n')
                    : ''}
                </p>
                <div className="mt-4">
                  {displayComment.disease_tags && (
                    <div className="mt-2">
                      <DiseaseTags tags={displayComment.disease_tags} />
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500 italic">この回のコメントはありません</p>
              </div>
            )
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-gray-500 italic">この馬のコメントは登録されていません</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};
