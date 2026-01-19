import React from 'react';
import Link from 'next/link';
import { Box, Typography, Tooltip } from '@mui/material';
import { BroodmareBadge } from '@/components/BroodmareBadge';

// コンポーネントの型定義
import type { Horse } from '../../types';

// ユーティリティ関数
import { 
  isUnsoldHorse,
  formatSeller,
  getDisplayPrice,
  formatPrize,
  getGrowthRate
} from '../../utils/formatters';
import { formatAge } from '../../utils/formatAge';
import { parseAuctionDate, formatDate } from '../../utils/dateUtils';
import SexBadge from '../SexBadge';

// 動的インポートのための型定義
interface HorseImageProps {
  src?: string | { image_url: string } | null;
  alt?: string;
  className?: string;
  [key: string]: any;
}

// 動的インポートでHorseImageを取得
let HorseImage: React.FC<HorseImageProps> = ({ src, alt = 'Horse image', className = '', ...props }) => {
  const [imgSrc, setImgSrc] = React.useState<string>('');
  
  React.useEffect(() => {
    if (src) {
      setImgSrc(typeof src === 'string' ? src : src?.image_url || '');
    }
  }, [src]);

  return (
    <div className={`relative w-full aspect-[3/2] bg-gray-100 rounded-t-lg overflow-hidden ${className}`} {...props}>
      {imgSrc ? (
        <img 
          src={imgSrc}
          alt={alt}
          className="absolute inset-0 w-full h-full object-cover"
          width={300}
          height={200}
          onError={(e) => {
            const target = e.target as HTMLImageElement;
            target.src = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0idz0iNiIgaGVpZ2h0PSI2Ij48cGF0aCBkPSJNMTggMTNoMS42ODNjLjU1OSAwIC45NTItLjU4MS43ODctMS4xNDNsLTEuNjUxLTQuODU0YTEuNSAxLjUgMCAwIDAtMS40MDItMS4wNDNoLTguMzE0YTEuNSAxLjUgMCAwIDAtMS40MDIgMS4wNDNsLTEuNjUgNC44NTRjLS4xNjUuNTYyLjIyOCAxLjE0My43ODcgMS4xNDNIM2ExIDEgMCAwIDAtMSAxdjhhMSAxIDAgMCAwIDEgMWgxNGExIDEgMCAwIDAgMS0xdi04YTEgMSAwIDAgMC0xLTF6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+';
          }}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-400">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 13h1.683c.559 0 .952-.581.787-1.143l-1.651-4.854a1.5 1.5 0 0 0-1.402-1.043h-8.314a1.5 1.5 0 0 0-1.402 1.043l-1.65 4.854c-.165.562.228 1.143.787 1.143H3a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-8a1 1 0 0 0-1-1z"></path>
            <circle cx="12" cy="10" r="3"></circle>
          </svg>
        </div>
      )}
    </div>
  );
};

interface HorseCardProps {
  horse: Horse;
  onHorseClick?: (horse: Horse) => void;
}

const HorseCard: React.FC<HorseCardProps> = ({ horse, onHorseClick }) => {
  const handleClick = (e: React.MouseEvent) => {
    // リンク以外の要素がクリックされた場合のみ処理を実行
    if ((e.target as HTMLElement).tagName !== 'A' && onHorseClick) {
      e.preventDefault();
      onHorseClick(horse);
    }
  };

  const latestAuction = horse.auction_histories?.[0];
  const isUnsold = isUnsoldHorse(horse);
  const displayPrice = getDisplayPrice(horse);
  
  // 成長率を計算（total_prize_startとtotal_prize_latestが必要）
  const growthRate = horse.total_prize_start && horse.total_prize_latest 
    ? getGrowthRate(
        typeof horse.total_prize_start === 'string' ? parseFloat(horse.total_prize_start) : horse.total_prize_start,
        typeof horse.total_prize_latest === 'string' ? parseFloat(horse.total_prize_latest) : horse.total_prize_latest
      )
    : null;
  
  // 年齢をフォーマット（性別と年齢が必要）
  const age = horse.age ? formatAge(horse.sex, horse.age) : '';
  const sex = horse.sex || '';
  const seller = formatSeller(horse.seller);
  const totalPrizeLatest = formatPrize(horse.total_prize_latest);

  return (
    <Link 
      href={`/horses/${horse.id}`} 
      passHref
      className="block bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-300"
      onClick={handleClick}
    >
      <Box component="div" className="relative">
        {/* 馬画像 */}
        <div className="relative">
          <HorseImage 
            src={horse.image_url} 
            alt={horse.name} 
            className="w-full h-48 object-cover"
          />
          {horse.is_broodmare && (
            <BroodmareBadge 
              variant="tag" 
              className="absolute top-3 left-3"
              ariaLabel="繁殖牝馬"
            />
          )}
        </div>

        {/* 馬の基本情報 */}
        <Box className="p-4">
          <Box className="flex justify-between items-start mb-2">
            <Typography variant="h6" className="font-bold text-gray-900 truncate flex items-center gap-2" title={horse.name}>
              {horse.is_broodmare && (
                <BroodmareBadge variant="circle" className="shrink-0" />
              )}
              <span>{horse.name}</span>
            </Typography>
            <SexBadge sex={sex} age={horse.age} />
          </Box>

          {/* 血統情報 */}
          <Box className="text-sm text-gray-600 mb-3 space-y-1">
            <p className="truncate" title={`父: ${horse.sire || '不明'}`}>父: {horse.sire || '不明'}</p>
            <p className="truncate" title={`母: ${horse.dam || '不明'}`}>母: {horse.dam || '不明'}</p>
            <p className="truncate" title={`母父: ${horse.dam_sire || '不明'}`}>母父: {horse.dam_sire || '不明'}</p>
          </Box>

          {/* オークション情報 */}
          <Box className="mt-4 pt-3 border-t border-gray-100">
            <Box className="flex justify-between items-center mb-1">
              <Typography variant="body2" className="text-gray-500">
                落札価格:
              </Typography>
              <Typography 
                variant="body1" 
                className={`font-semibold ${isUnsold ? 'text-red-600' : 'text-blue-600'}`}
              >
                {displayPrice}
              </Typography>
            </Box>

            {growthRate !== null && growthRate !== undefined && (
              <Box className="flex justify-between items-center mb-1">
                <Typography variant="body2" className="text-gray-500">
                  成長率:
                </Typography>
                <Typography 
                  variant="body2" 
                  className={`font-medium ${parseFloat(growthRate) > 0 ? 'text-green-600' : 'text-red-600'}`}
                >
                  {growthRate}
                </Typography>
              </Box>
            )}

            {horse.total_prize_start ? (
              <Box className="flex justify-between items-center mb-1">
                <Typography variant="body2" className="text-gray-500">
                  落札時の賞金:
                </Typography>
                <Typography variant="body2" className="font-medium text-gray-900">
                  {(Number(horse.total_prize_start) / 10000).toLocaleString('ja-JP')}万円
                </Typography>
              </Box>
            ) : null}

            {seller && (
              <Box className="flex justify-between items-center">
                <Typography variant="body2" className="text-gray-500">
                  販売者:
                </Typography>
                <Tooltip title={seller} placement="top">
                  <Typography 
                    variant="body2" 
                    className="font-medium text-gray-900 truncate max-w-[150px]"
                  >
                    {seller}
                  </Typography>
                </Tooltip>
              </Box>
            )}

          </Box>
        </Box>
      </Box>
    </Link>
  );
};

export default HorseCard;
