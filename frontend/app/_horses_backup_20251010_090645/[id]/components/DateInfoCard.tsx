import React from 'react';
import { Card, CardHeader, CardContent, Typography } from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

// 日付フォーマット用のヘルパー関数
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return '-';
  try {
    return format(new Date(dateString), 'yyyy/MM/dd', { locale: ja });
  } catch (e) {
    console.error('日付のフォーマットに失敗しました:', e);
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
