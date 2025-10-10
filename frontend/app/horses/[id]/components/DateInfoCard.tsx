import React from 'react';
import { Card, CardHeader, CardContent, Typography } from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

// 日付フォーマット用のヘルパー関数
const formatDate = (dateString: string | string[] | null | undefined): string => {
  if (!dateString) return '-';
  
  try {
    let dateToFormat: string;
    
    // 配列の場合は最初の要素を使用
    if (Array.isArray(dateString)) {
      dateToFormat = dateString[0];
    } 
    // JSON文字列の配列の場合（例: '["2025-10-10"]'）
    else if (typeof dateString === 'string' && dateString.startsWith('[') && dateString.endsWith(']')) {
      try {
        const parsedArray = JSON.parse(dateString);
        dateToFormat = Array.isArray(parsedArray) ? parsedArray[0] : dateString;
      } catch {
        dateToFormat = dateString;
      }
    } else {
      dateToFormat = dateString;
    }
    
    // 日付オブジェクトに変換してフォーマット
    const date = new Date(dateToFormat);
    if (isNaN(date.getTime())) return '-';
    
    return format(date, 'yyyy/MM/dd', { locale: ja });
  } catch (e) {
    console.error('日付のフォーマットに失敗しました:', e, '入力値:', dateString);
    return '-';
  }
};

interface DateInfoCardProps {
  auctionDate?: string | null;
  createdAt: string;
  updatedAt?: string | null;
}

const DateInfoCard: React.FC<DateInfoCardProps> = ({
  auctionDate,
  createdAt,
  updatedAt,
}) => {
  return (
    <Card sx={{ '& .MuiCardHeader-root': { padding: 0, margin: 0 } }}>
      <CardHeader>
        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>
          データ情報
        </Typography>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        {auctionDate && (
          <div className="flex justify-between">
            <span className="text-gray-600">オークション日:</span>
            <span>{formatDate(auctionDate)}</span>
          </div>
        )}
        <div className="flex justify-between">
          <span className="text-gray-600">作成日:</span>
          <span>{formatDate(createdAt || new Date().toISOString())}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-600">更新日:</span>
          <span>{formatDate(updatedAt || createdAt || new Date().toISOString())}</span>
        </div>
      </CardContent>
    </Card>
  );
};

export default DateInfoCard;
