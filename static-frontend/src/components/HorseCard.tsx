import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Horse, AuctionHistory } from '@/types/horse';

// 血統情報から指定された種類の馬名を抽出する関数
const extractPedigree = (text: string | undefined, type: 'sire' | 'dam' | 'damsire'): string => {
  if (!text) return '';
  
  // 各タイプに応じた正規表現パターンを定義
  const patterns = {
    // 父：の直後の空白以外の文字列（全角スペースを含む）を取得
    sire: /父[：:]([^\s　]+(?:[ 　][^\s　]+)*)/,
    // 母：の直後の空白以外の文字列（全角スペースを含む）を取得
    dam: /母[：:]([^\s　]+(?:[ 　][^\s　]+)*)/,
    // 母の父：の直後の空白以外の文字列（全角スペースを含む）を取得
    damsire: /(?:母の?父|母父)[：:]([^\s　]+(?:[ 　][^\s　]+)*)/
  };
  
  // 指定されたタイプのパターンで検索
  const match = text.match(patterns[type]);
  if (match && match[1]) {
    return match[1].trim();
  }
  
  // パターンに一致しない場合は、タイプに応じたデフォルト値を返す
  if (type === 'sire' && text.includes('父：')) {
    return text.split('父：')[1].split(/[\s　]/)[0];
  }
  if (type === 'dam' && text.includes('母：')) {
    return text.split('母：')[1].split(/[\s　]/)[0];
  }
  if (type === 'damsire' && (text.includes('母の父：') || text.includes('母父：'))) {
    const delimiter = text.includes('母の父：') ? '母の父：' : '母父：';
    return text.split(delimiter)[1].split(/[\s　]/)[0];
  }
  
  // いずれにも該当しない場合は空文字を返す
  return '';
};

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

  // 最新のオークション情報を取得（propsから受け取る）
  const latestAuction = horse.latest_auction || getLatestAuction();
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
      <div className="mt-4 space-y-3">
        {/* 1行目: 馬名、年齢、性別、落札価格 */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm text-gray-700">
            <span className="font-semibold">{horse.name}</span>
            <span className="ml-2 text-gray-500">{horse.age}歳</span>
            <span className="ml-2">
              <Badge variant="outline">{horse.sex}</Badge>
            </span>
          </h3>
          <p className="text-sm font-medium text-gray-900">
            {displayPrice(price, isUnsold)}
          </p>
        </div>
        
        {/* 2行目: 2カラムレイアウト */}
        <div className="grid grid-cols-2 gap-4">
          {/* 左カラム: 血統情報 */}
          <div className="text-sm text-gray-600 space-y-1 overflow-hidden">
            <p className="whitespace-nowrap overflow-hidden text-ellipsis">父：{horse.sire || '不明'}</p>
            <p className="whitespace-nowrap overflow-hidden text-ellipsis">母：{horse.dam || '不明'}</p>
            {(horse.damsire && horse.damsire !== '不明') && (
              <p className="whitespace-nowrap overflow-hidden text-ellipsis">母父：{horse.damsire}</p>
            )}
          </div>
          
          {/* 右カラム: 総賞金と馬体重 */}
          <div className="text-sm text-gray-500 space-y-1">
            {latestAuction?.total_prize_latest !== undefined && (
              <p>総賞金: {latestAuction.total_prize_latest.toLocaleString()}万円</p>
            )}
            {latestAuction?.weight && latestAuction.weight > 0 && (
              <p>{latestAuction.weight}kg</p>
            )}
          </div>
        </div>
        
        {/* 3行目: 疾病情報 */}
        {horse.disease_tags && horse.disease_tags.length > 0 && (
          <div className="pt-1">
            <div className="flex flex-wrap gap-1">
              {horse.disease_tags.map((tag, index) => (
                <Badge key={index} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
