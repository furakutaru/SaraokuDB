import React from 'react';
import { Badge } from '@/components/ui/badge';
import { Horse, AuctionHistory } from '@/types/horse';
import { formatSex, getSexColor } from '@/utils/normalize';
import { formatPrizeMan } from '@/utils/format';

// HorseWithAuction 型を拡張
interface HorseWithAuction extends Horse {
  latest_auction?: AuctionHistory | null;
  disease_tags?: string[];
  race_record?: string | null;
}

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
  horse: HorseWithAuction;
  auctionHistory?: AuctionHistory[];
  onClick: () => void;
}

export default function HorseCard({ horse, auctionHistory = [], onClick }: HorseCardProps) {
  // 最新のオークション履歴を取得
  const latestAuction = horse.latest_auction || null;

  // 最新のオークション情報を取得
  const getLatestAuction = (): AuctionHistory | null => {
    return latestAuction;
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

  // 価格を表示用にフォーマット（落札価格は「¥1,000」形式で表示）
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
        return '¥' + priceNum.toLocaleString('ja-JP');
      }
    }
    
    // 最新の価格を取得
    const latestPrice = getLatestSoldPrice();
    if (latestPrice !== null) {
      console.log(`  Using latest price: ${latestPrice}`);
      return '¥' + latestPrice.toLocaleString('ja-JP');
    }
    
    // 価格が見つからない場合はハイフンを表示
    return '-';
  };

  // 最新のオークション情報を取得（propsから受け取る）
  const latestAuctionInfo = getLatestAuction();
  const price = latestAuctionInfo?.sold_price ?? horse.sold_price ?? null;
  const isUnsold = latestAuctionInfo?.is_unsold ?? horse.is_unsold ?? false;
  
  // 血統情報を抽出（直接のプロパティを使用）
  const sire = horse.sire || '';
  const dam = horse.dam || '';
  const damsire = horse.damsire || '';

  // 病気タグの有無をチェック
  const hasDiseaseTags = Array.isArray(horse.disease_tags) && horse.disease_tags.length > 0;

  return (
    <div className="relative group cursor-pointer" onClick={onClick}>
      <div className="aspect-w-3 aspect-h-2 w-full overflow-hidden rounded-lg bg-gray-200">
        <img
          src={
            typeof horse.image_url === 'string' 
              ? horse.image_url 
              : (horse.image_url as any)?.image_url || '/placeholder-horse.jpg'
          }
          alt={horse.name || 'Unknown Horse'}
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
              <Badge variant="outline" className={getSexColor(horse.sex)}>
                {formatSex(horse.sex)}
              </Badge>
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
            <div className="grid grid-cols-2 gap-1">
              <div>父: {sire || '不明'}</div>
              <div>母: {dam || '不明'}</div>
              <div>母父: {damsire || '不明'}</div>
            </div>
          </div>
          
          {/* 右カラム: 総賞金と馬体重 */}
          <div className="text-sm text-gray-500 space-y-1">
            {latestAuctionInfo?.total_prize_latest !== undefined && (
              <p>総賞金: {formatPrizeMan(latestAuctionInfo.total_prize_latest)}</p>
            )}
            {latestAuctionInfo?.weight && latestAuctionInfo.weight > 0 && (
              <p>{latestAuctionInfo.weight}kg</p>
            )}
          </div>
        </div>
        
        {/* 3行目: 疾病情報 */}
        {hasDiseaseTags && (
          <div className="flex flex-wrap gap-1 mt-2">
            {horse.disease_tags?.map((tag, index) => (
              <Badge key={index} variant="secondary" className="text-xs">
                {tag}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
