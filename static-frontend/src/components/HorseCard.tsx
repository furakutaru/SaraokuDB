import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Horse, AuctionHistory } from '@/types/horse';

interface HorseCardProps {
  horse: Horse;
  auctionHistory?: AuctionHistory[];
  onClick: () => void;
}

export default function HorseCard({ horse, auctionHistory = [], onClick }: HorseCardProps) {
  // この馬に関連するオークション履歴を取得
  const getHorseAuctionHistory = (): AuctionHistory[] => {
    if (!auctionHistory || auctionHistory.length === 0) return [];
    return auctionHistory
      .filter(history => history.horse_id === horse.id)
      .sort((a, b) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime());
  };

  // 最新のオークション情報を取得
  const getLatestAuction = (): AuctionHistory | null => {
    const history = getHorseAuctionHistory();
    return history.length > 0 ? history[0] : null;
  };

  // 最新の落札価格を取得
  const getLatestSoldPrice = (): number | null => {
    const latestAuction = getLatestAuction();
    if (!latestAuction) return null;
    
    const price = latestAuction.sold_price;
    if (price === null || price === undefined) return null;
    
    const priceNum = typeof price === 'number' ? price : Number(price);
    return isNaN(priceNum) ? null : priceNum;
  };

  // 価格を表示用にフォーマット
  const displayPrice = (price: number | null | undefined, isUnsold: boolean = false) => {
    console.log(`Displaying price for ${horse.name}:`, { 
      price, 
      isUnsold,
      latestAuction: getLatestAuction()
    });
    
    // 主取りの場合は即座に返す
    if (isUnsold === true) {
      console.log('  Marked as unsold, showing 主取り');
      return '主取り';
    }
    
    // 価格を表示
    if (price !== null && price !== undefined) {
      const priceNum = typeof price === 'number' ? price : Number(price);
      if (!isNaN(priceNum) && priceNum > 0) {
        console.log(`  Using provided price: ${priceNum}`);
        return '¥' + priceNum.toLocaleString();
      }
    }
    
    // 最新の価格を取得
    const latestPrice = getLatestSoldPrice();
    if (latestPrice !== null) {
      console.log(`  Using latest price: ${latestPrice}`);
      return '¥' + latestPrice.toLocaleString();
    }
    
    // 価格が見つからない場合はハイフンを表示
    return '-';
  };

  // 最新のオークション情報を取得
  const latestAuction = getLatestAuction();
  const price = latestAuction?.sold_price ?? null;
  const isUnsold = latestAuction?.is_unsold ?? false;
  
  // 病気タグの有無をチェック
  const hasDiseaseTags = horse.disease_tags && horse.disease_tags.length > 0;

  return (
    <div className="relative group cursor-pointer" onClick={onClick}>
      <div className="aspect-w-3 aspect-h-2 w-full overflow-hidden rounded-lg bg-gray-200">
        <img
          src={horse.image_url || '/placeholder-horse.jpg'}
          alt={horse.name}
          className="h-48 w-full object-cover object-center group-hover:opacity-75"
        />
        {isUnsold && (
          <div className="absolute top-2 right-2 bg-yellow-500 text-white text-xs font-bold px-2 py-1 rounded">
            主取り
          </div>
        )}
      </div>
      <div className="mt-4 flex justify-between">
        <div>
          <h3 className="text-sm text-gray-700">
            <span className="font-semibold">{horse.name}</span>
            <span className="ml-2 text-gray-500">{horse.age}歳</span>
            <span className="ml-2">
              <Badge variant="outline">{horse.sex}</Badge>
            </span>
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {horse.sire} - {horse.dam}
          </p>
          <p className="text-xs text-gray-500">母父: {horse.damsire}</p>
          {horse.disease_tags && horse.disease_tags.length > 0 && (
            <div className="mt-1 flex flex-wrap gap-1">
              {horse.disease_tags.map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>
        <div className="text-right">
          <p className="text-sm font-medium text-gray-900">
            {displayPrice(price, isUnsold)}
          </p>
          {latestAuction?.total_prize_latest && latestAuction.total_prize_latest > 0 && (
            <p className="text-xs text-gray-500">
              総賞金: {latestAuction.total_prize_latest.toLocaleString()}万円
            </p>
          )}
          {latestAuction?.weight && latestAuction.weight > 0 && (
            <p className="text-xs text-gray-500">馬体重: {latestAuction.weight}kg</p>
          )}
          {latestAuction?.seller && (
            <p className="text-xs text-gray-500">売主: {latestAuction.seller}</p>
          )}
        </div>
      </div>
    </div>
  );
}
