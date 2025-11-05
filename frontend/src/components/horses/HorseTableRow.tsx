import Link from 'next/link';
import { formatDate, formatPrice, formatManYen } from '../../utils/format';
import type { RaceRecordInfo } from '@/components/common/AuctionPrizeDisplay';
import { getSexColor, formatSex } from '@/utils/sex';
import type { HorseWithCalculations } from '@/types/horse';
import AuctionPrizeDisplay from '@/components/common/AuctionPrizeDisplay';

type HorseTableRowProps = {
  horse: HorseWithCalculations;
  onRowClick: (id: string | number) => void;
};

export const HorseTableRow = ({ horse, onRowClick }: HorseTableRowProps) => {
  console.log('HorseTableRow - horse.race_record:', horse.race_record);
  const handleClick = (e: React.MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName !== 'A' && target.tagName !== 'A') {
      onRowClick(horse.id);
    }
  };

  // 病歴の有無を判定
  const hasDisease = (tags: any[] | string | null | undefined): boolean => {
    // タグが配列でない場合は、文字列に変換して判定
    if (!tags) return false;
    if (typeof tags === 'string') {
      const strTag = tags.trim();
      return !(strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。');
    }
    if (!Array.isArray(tags) || tags.length === 0) return false;
    return tags.some(tag => {
      const strTag = String(tag).trim();
      return !(strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。');
    });
  };

  // formatManYen を AuctionPrizeDisplay の formatPrizeMan プロップに渡せる形式に変換
  const formatPrizeManWrapper = (amount: string | number | null | undefined, _raceRecords?: RaceRecordInfo | null): string => {
    if (amount === null || amount === undefined) return '-';
    const numAmount = typeof amount === 'string' ? parseFloat(amount) : amount;
    if (isNaN(numAmount)) return '-';
    return formatManYen(numAmount);
  };

  // 性別のフォーマットはutils/sex.tsのformatSex関数を使用

  // 年齢を表示
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return `${age}歳`;
  };

  // 体重を表示
  const displayWeight = (weight: string | number | null | undefined): string => {
    if (weight === null || weight === undefined || weight === '') return '-';
    
    const weightStr = String(weight);
    const numWeight = parseFloat(weightStr.replace(/[^0-9.]/g, ''));
    
    if (!isNaN(numWeight) && isFinite(numWeight)) {
      return `${Math.round(numWeight)} kg`;
    }
    
    const trimmedWeight = weightStr.trim();
    if (trimmedWeight !== '') {
      return trimmedWeight.toLowerCase().includes('kg') ? trimmedWeight : `${trimmedWeight} kg`;
    }
    
    return '-';
  };

  // ROIを計算
  const calcROI = (prizeLatest: number | null | undefined, prizeStart: number | null | undefined, price: any): string => {
    if (prizeLatest === null || prizeLatest === undefined || prizeStart === null || prizeStart === undefined) return '-';
    
    const numPrice = price === null || price === undefined ? 0 : (typeof price === 'string' ? parseFloat(price) : price);
    if (isNaN(numPrice) || numPrice <= 0) return '-';
    
    const earnedPrize = prizeLatest - prizeStart;
    const rio = (earnedPrize * 10000) / numPrice;
    return (rio * 100).toFixed(1) + '%';
  };

  // 詳細ページのURLを取得
  const getDetailUrl = (horse: any): string | undefined => {
    return horse.detail_url || horse.auction_url || undefined;
  };

  return (
    <tr 
      key={horse.id} 
      className="hover:bg-blue-50 cursor-pointer"
      onClick={handleClick}
    >
      <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">
        <Link 
          href={`/horses/${horse.id}`} 
          className="hover:underline text-blue-700 whitespace-nowrap"
          onClick={(e) => e.stopPropagation()}
        >
          {horse.name}
        </Link>
      </td>
      <td className="px-3 py-2">
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${getSexColor(horse.sex)}`}>
          {formatSex(horse.sex || '')}
        </span>
      </td>
      <td className="px-3 py-2">{displayAge(horse.age)}</td>
      <td className="px-3 py-2">{horse.sire || '-'}</td>
      <td className="px-3 py-2 text-right">
        {displayWeight(horse.weight)}
      </td>
      <td className="px-3 py-2">
        {formatPrice(
          horse.sold_price, 
          horse.is_unsold || horse.unsold || (horse.unsold_count || 0) > 0, // isUnsoldパラメータ
          false, 
          horse.sold_price, 
          0
        )}
      </td>
      <td className="px-3 py-2">
        <AuctionPrizeDisplay
          raceRecord={{
            ...(typeof horse.race_record === 'string' 
              ? JSON.parse(horse.race_record) 
              : horse.race_record || {}),
            // トップレベルの unified_race_records も含める
            unified_race_records: horse.unified_race_records,
            // デバッグ用に horse オブジェクト全体をログに出力
            _debug_horse: JSON.parse(JSON.stringify(horse))
          }}
          totalPrizeStart={horse.total_prize_start}
          isUnsold={horse.is_unsold || horse.unsold || (horse.unsold_count || 0) > 0}
          formatPrizeMan={formatPrizeManWrapper}
        />
      </td>
      <td className="px-3 py-2">
        {formatPrice(
          horse.total_prize_latest, 
          horse.is_unsold || horse.unsold || (horse.unsold_count || 0) > 0,
          false,
          horse.total_prize_latest,
          0
        )}
      </td>
      <td className="px-3 py-2">
        {calcROI(horse.total_prize_latest, horse.total_prize_start, horse.sold_price)}
      </td>
      <td className="px-3 py-2">
        <div className="flex flex-col gap-1 items-center">
          {horse.jbis_url && horse.jbis_url.trim() !== '' && (
            <a 
              href={horse.jbis_url} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-xs text-blue-600 underline whitespace-nowrap"
              onClick={(e) => e.stopPropagation()}
            >
              JBIS
            </a>
          )}
          {getDetailUrl(horse) && (
            <a 
              href={getDetailUrl(horse)} 
              target="_blank" 
              rel="noopener noreferrer" 
              className="text-xs text-blue-600 underline whitespace-nowrap"
              onClick={(e) => e.stopPropagation()}
            >
              サラオク
            </a>
          )}
        </div>
      </td>
      <td className="px-3 py-2 text-center">
        {!hasDisease(horse.disease_tags) ? (
          <span className="text-xs font-medium bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">
            なし
          </span>
        ) : (
          <span className="text-xs font-medium bg-pink-100 text-pink-800 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">
            あり
          </span>
        )}
      </td>
    </tr>
  );
};
