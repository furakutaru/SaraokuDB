import React from 'react';
import { Typography, Button, Card, CardHeader, CardContent } from '@mui/material';
import Link from 'next/link';

export interface AuctionHistory {
  auction_date?: string;
  sold_price?: number | null;
  unsold?: boolean;
  detail_url?: string | null;
  [key: string]: any;
}

interface AuctionHistoryCardProps {
  history: AuctionHistory[];
  formatDate: (date: string) => string;
  formatPrizeMan: (price: number) => string;
}

const AuctionHistoryCard: React.FC<AuctionHistoryCardProps> = ({
  history,
  formatDate,
  formatPrizeMan,
}) => {
  if (!history?.length) {
    return <p className="text-gray-500">オークション履歴がありません</p>;
  }

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
                    {formatDate(item.auction_date || '')}
                  </Typography>
                  <p className="text-sm text-gray-500">
                    落札価格: {item.unsold ? '不成立' : formatPrizeMan(item.sold_price || 0)}
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
