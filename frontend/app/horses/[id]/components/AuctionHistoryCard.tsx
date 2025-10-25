import React from 'react';
import { Typography, Button, Card, CardHeader, CardContent } from '@mui/material';
import Link from 'next/link';

export interface AuctionHistory {
  id?: string | number;
  horse_id?: string | number;
  auction_date: string | string[];  // string または string[] を許容
  price?: number | null;  // データベースの price カラムにマッピング（優先的に使用）
  sold_price?: number | null; // 後方互換性のため残す（非推奨）
  total_prize_start?: number;
  total_prize_latest?: number;
  weight?: number | null;
  seller?: string | null;
  is_unsold?: boolean;
  unsold?: boolean;
  comment?: string;
  created_at?: string;
  updated_at?: string;
  detail_url?: string | null;
  auction_url?: string;
  name?: string;
  sex?: string;
  age?: string | number;
  race_record?: any;
  primary_image?: string;
  disease_tags?: string;
  [key: string]: any;
}

interface AuctionHistoryCardProps {
  history: AuctionHistory[];
  formatDate: (date: string) => string;
  formatPrizeMan: (price: number | string | null | undefined, isUnsold?: boolean) => string;
}

const AuctionHistoryCard: React.FC<AuctionHistoryCardProps> = ({
  history,
  formatDate,
  formatPrizeMan,
}) => {
  if (!history?.length) {
    return <p className="text-gray-500">オークション履歴がありません</p>;
  }

  // auction_date を文字列に正規化するヘルパー関数
  const normalizeAuctionDate = (date: string | string[] | undefined): string => {
    if (!date) return '';
    if (Array.isArray(date)) return date[0] || '';
    return date;
  };

  return (
    <Card>
      <CardHeader>
        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>
          オークション履歴
        </Typography>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {history.map((item, index) => (
            <div key={index} className="border-b pb-4 last:border-b-0 last:pb-0">
              <div className="flex justify-between items-start">
                <div>
                  <Typography variant="h6" component="h4" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>
                    {formatDate(normalizeAuctionDate(item.auction_date))}
                  </Typography>
                  <p className="text-sm text-gray-500">
                    落札価格: {formatPrizeMan(item.price ?? item.sold_price, item.unsold || item.is_unsold)}
                  </p>
                </div>
                {item.detail_url && (
                  <Button 
                    component={Link}
                    href={item.detail_url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="outlined" 
                    size="small"
                    className="whitespace-nowrap"
                  >
                    詳細を見る
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
};

export default AuctionHistoryCard;
