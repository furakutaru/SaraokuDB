import React from 'react';
import { Typography, Card, CardHeader, CardContent, Box } from '@mui/material';

export interface PriceCardProps {
  horse: {
    sold_price?: number | null;
    unsold?: boolean;
    unsold_count?: number;
    history: Array<{
      auction_date: string;
      sold_price?: number | null;
      unsold?: boolean;
      race_record?: string;
      seller?: string;
    }>;
  };
  formatManYen: (price: number) => string;
  formatDate: (date: string) => string;
}

const PriceCard: React.FC<PriceCardProps> = ({ 
  horse, 
  formatManYen,
  formatDate
}) => {
  const latestHistory = horse.history?.[0] || null;
  
  // 前回のオークション情報を取得（履歴が2件以上ある場合）
  const previousAuction = horse.history && horse.history.length > 1 ? horse.history[1] : null;
  
  return (
    <Card className="mb-6">
      <CardHeader 
        sx={{
          padding: 0,
          margin: 0,
          '& .MuiCardHeader-content': {
            padding: 0,
            margin: 0
          }
        }}
      >
        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>落札価格</Typography>
      </CardHeader>
      <CardContent className="relative">
        {(() => {
          if (process.env.NODE_ENV === 'development') {
            console.log('latestHistory:', JSON.stringify({
              sold_price: latestHistory?.sold_price,
              unsold: latestHistory?.unsold,
              history: latestHistory,
              horse_history: horse.history
            }, null, 2));
          }
          return null;
        })()}
        <div className="space-y-4">
          {/* 主取り回数表示（1回以上の場合のみ表示） */}
          {(horse.unsold_count ?? 0) > 0 && (
            <div className="text-center text-blue-600 font-bold">主取り{horse.unsold_count}回</div>
          )}
          
          {/* 落札価格（最新） */}
          <div className="text-center">
            <div className="text-sm text-gray-600 mb-1">落札価格</div>
            <div className="text-red-600 text-3xl font-extrabold">
              {(() => {
              // 主取りの場合は「主取り」と表示
              const soldPrice = latestHistory?.sold_price;
              
              // 型を明示的に変換して比較
              const unsoldValue = latestHistory?.unsold;
              const isUnsold = Boolean(unsoldValue) && (
                unsoldValue === true || 
                Number(unsoldValue) === 1 || 
                String(unsoldValue).trim() === '1' ||
                String(unsoldValue).toLowerCase() === 'true'
              );
              
              // 数値に変換して比較
              const soldPriceNum = soldPrice === null || soldPrice === undefined 
                ? null 
                : Number(soldPrice);
              
              if (isUnsold || 
                  soldPrice === null ||
                  soldPrice === undefined ||
                  soldPriceNum === 0 ||
                  String(soldPrice).trim() === '0' ||
                  String(soldPrice).toLowerCase() === 'null' ||
                  String(soldPrice) === '[null]') {
                return '主取り';
              }
              
              // sold_price が配列の場合は最後の有効な価格を使用
              if (Array.isArray(latestHistory?.sold_price)) {
                const validPrices = latestHistory.sold_price
                  .map(price => Number(price))
                  .filter(price => !isNaN(price) && price > 0);
                
                if (validPrices.length > 0) {
                  return `¥${validPrices[validPrices.length - 1].toLocaleString()}`;
                }
              } 
              // sold_price が文字列の場合
              else if (latestHistory?.sold_price) {
                const soldPrice = latestHistory.sold_price;
                
                // 文字列に変換
                const priceStr = String(soldPrice);
                
                // "[null]" または "null" の場合は主取りと表示
                if (priceStr === '[null]' || priceStr === 'null') {
                  return '主取り';
                }
                
                // 数値に変換可能な場合は数値として表示
                const numericStr = priceStr.replace(/[^0-9.-]+/g, '');
                const price = Number(numericStr);
                
                if (!isNaN(price) && price > 0) {
                  return `¥${price.toLocaleString()}`;
                }
              }
              // sold_price が数値の場合
              else if (latestHistory?.sold_price) {
                const price = Number(latestHistory.sold_price);
                if (!isNaN(price) && price > 0) {
                  return `¥${price.toLocaleString()}`;
                }
              }
              
              return '主取り';
            })()}
            </div>
          </div>
          
          {/* 前回の落札価格 */}
          {horse.history.length > 1 && (
            <div className="text-center">
              <div className="text-sm text-gray-600">前回の落札価格</div>
              <div className="text-lg font-semibold">
                {(() => {
                  const prevAuction = horse.history[1];
                  if (!prevAuction) return 'データなし';
                  
                  // 型を明示的に変換して比較
                  const unsoldValue = prevAuction.unsold;
                  const isUnsold = Boolean(unsoldValue) && (
                    unsoldValue === true || 
                    Number(unsoldValue) === 1 || 
                    String(unsoldValue).trim() === '1' ||
                    String(unsoldValue).toLowerCase() === 'true'
                  );
                  
                  if (isUnsold) return '主取り';
                  
                  const prevPrice = prevAuction.sold_price;
                  if (!prevPrice) return 'データなし';
                  
                  // 数値に変換
                  const price = Number(prevPrice);
                  if (isNaN(price) || price <= 0) return 'データなし';
                  
                  return `¥${price.toLocaleString()}`;
                })()}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
        
  );
};

export default PriceCard;
