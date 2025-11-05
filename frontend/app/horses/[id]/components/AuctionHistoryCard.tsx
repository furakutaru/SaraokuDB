import React from 'react';
import { Typography, Button, Card, CardHeader, CardContent } from '@mui/material';
import { format } from 'date-fns';
import Link from 'next/link';
import { formatPrize } from '@/utils/format';

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

  // auction_date をフォーマット済みの文字列に変換するヘルパー関数
  const formatAuctionDate = (date: string | string[] | undefined): string => {
    console.log('formatAuctionDate input:', date);
    
    if (!date) return '';
    
    let dateStr: string;
    
    try {
      // 配列の場合は最初の要素を取得
      if (Array.isArray(date)) {
        dateStr = date[0];
      } 
      // JSON文字列の配列の場合（例: '["2025-10-26"]'）
      else if (typeof date === 'string') {
        // まずJSONとしてパースを試みる
        try {
          const parsed = JSON.parse(date);
          dateStr = Array.isArray(parsed) ? parsed[0] : parsed;
          console.log('Parsed JSON date:', dateStr);
        } catch (e) {
          // JSONとしてパースできない場合はそのまま使用
          dateStr = date;
        }
      } else {
        dateStr = String(date);
      }
      
      // 余分な文字を削除（[ ] " ' など）
      dateStr = dateStr
        .replace(/^\[|\]$/g, '')  // 先頭と末尾の角括弧を削除
        .replace(/^"|"$/g, '')    // 先頭と末尾のダブルクォーテーションを削除
        .replace(/^'|'$/g, '')     // 先頭と末尾のシングルクォーテーションを削除
        .trim();
      
      console.log('Cleaned date string:', dateStr);
      
      // 日付オブジェクトに変換してフォーマット
      const dateObj = new Date(dateStr);
      if (!isNaN(dateObj.getTime())) {
        const formatted = format(dateObj, 'yyyy/MM/dd');
        console.log('Formatted date:', formatted);
        return formatted;
      } else {
        console.warn('Invalid date object for:', dateStr);
      }
    } catch (e) {
      console.error('Error formatting date:', e, 'Input:', date);
    }
    
    // 有効な日付でない場合は元の文字列を返す
    console.log('Returning original date as fallback:', date);
    return typeof date === 'string' ? date : JSON.stringify(date);
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
                    {formatAuctionDate(item.auction_date)}
                  </Typography>
                  <div className="text-base font-medium">
                    落札時賞金:{" "}
                    <span className="font-bold">
                      {formatPrizeMan(history[0].total_prize_start, {
                        ...history[0].race_record,
                        // @ts-ignore - 型エラーを無視
                        unified_race_records: history[0].unified_race_records,
                        is_unsold: history[0].is_unsold || history[0].unsold || (history[0].unsold_count || 0) > 0
                      })}
                    </span>
                  </div>
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
