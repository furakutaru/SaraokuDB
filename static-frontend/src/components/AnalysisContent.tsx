'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Horse, AuctionHistory } from '@/types/horse';
import { useNormalize } from '@/hooks/useNormalize';

// フロントエンドで使用する馬の型（Horse型を拡張）
interface HorseWithAuction extends Horse {
  // フロントエンドで使用する追加プロパティ
  dam_sire: string; // damsireのエイリアス
  detail_url: string; // auction_urlのエイリアス
  comment?: string; // コメント
  // オークション情報（将来的な機能拡張用）
  latestAuction?: AuctionHistory;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean;
  auction_date?: string;
  seller?: string;
  // Horseインターフェースのプロパティをオーバーライド
  sold_price?: number | null;
}

// 正規化関数を使用するため、独自のフォーマット関数を削除

interface HorseData {
  horses: Horse[];
  auction_history: AuctionHistory[];
  metadata: {
    total_horses: number;
    total_auctions: number;
    average_price: number;
    last_updated: string;
  };
}

export default function AnalysisContent() {
  const normalize = useNormalize();
  const [data, setData] = useState<HorseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showType, setShowType] = useState<'all' | 'roi' | 'value'>('all');
  const [sortKey, setSortKey] = useState<string>('');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const router = useRouter();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // 両方のJSONを並行して取得
        const [horsesResponse, auctionHistoryResponse] = await Promise.all([
          fetch('/data/horses.json'),
          fetch('/data/auction_history.json')
        ]);

        if (!horsesResponse.ok || !auctionHistoryResponse.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const horsesData = await horsesResponse.json();
        const auctionHistory = await auctionHistoryResponse.json();

        // オークション履歴を馬IDでグループ化
        const auctionHistoryByHorseId = auctionHistory.reduce((acc: Record<string, AuctionHistory[]>, history: AuctionHistory) => {
          if (!acc[history.horse_id]) {
            acc[history.horse_id] = [];
          }
          acc[history.horse_id].push(history);
          return acc;
        }, {});
        
        // 馬データにオークション履歴をマージ
        const horsesWithHistory = (horsesData.horses || []).map((horse: Horse) => {
          const history = auctionHistoryByHorseId[horse.id] || [];
          const latestAuction = history[0]; // 最新のオークション情報
          
          return {
            ...horse,
            latest_auction: latestAuction || null,
            sold_price: latestAuction?.sold_price || null,
            is_unsold: latestAuction?.is_unsold || false,
            auction_date: latestAuction?.auction_date || horse.auction_date,
            seller: latestAuction?.seller || horse.seller,
            weight: latestAuction?.weight || horse.weight,
            total_prize_start: latestAuction?.total_prize_start || horse.total_prize_start,
            total_prize_latest: latestAuction?.total_prize_latest || horse.total_prize_latest,
            comment: latestAuction?.comment || horse.comment
          };
        });

        setData({
          horses: horsesWithHistory,
          auction_history: auctionHistory,
          metadata: horsesData.metadata || {
            total_horses: horsesWithHistory.length,
            total_auctions: auctionHistory.length,
            average_price: auctionHistory.length > 0 
              ? auctionHistory.reduce((sum: number, h: AuctionHistory) => sum + (h.sold_price || 0), 0) / auctionHistory.length
              : 0,
            last_updated: new Date().toISOString()
          }
        });
      } catch (e: any) {
        console.error('データ取得エラー:', e);
        setError('データの読み込みに失敗しました: ' + e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  if (error || !data) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error || 'データがありません'}</div>;
  }

  // 馬データを処理（オークション履歴は将来的な機能拡張のために型定義のみ残す）
  const horsesWithLatest: HorseWithAuction[] = data.horses.map(horse => {
    // オークション情報は現在使用しないが、将来的な拡張のために型は残す
    return {
      ...horse,
      // 互換性のためのプロパティマッピング
      dam_sire: horse.damsire || '',
      detail_url: horse.auction_url || '',
      // オークション情報（将来的な機能拡張用）
      latestAuction: undefined,
      total_prize_start: horse.total_prize_start || 0,
      total_prize_latest: horse.total_prize_latest || 0,
      is_unsold: false,
      auction_date: '',
      seller: '',
      sold_price: horse.sold_price || 0,
      weight: horse.weight || null
    };
  });

  // すべての馬を表示（現在は主取り馬のフィルタリングは行わない）
  let horses = horsesWithLatest;

  // サマリー - RIO計算を詳細ページと合わせる
  const avgRIO = horses.length > 0 ? (
    horses.reduce((sum, h) => {
      let soldPrice = 0;
      const price = h.sold_price;
      
      // sold_priceの型を安全に処理
      if (price !== null && price !== undefined) {
        if (typeof price === 'number') {
          soldPrice = price;
        } else if (typeof price === 'string') {
          // 文字列から数値のみを抽出
          const numStr = String(price).replace(/[^0-9]/g, '') || '0';
          soldPrice = parseInt(numStr, 10) || 0;
        }
      }
      
      const prizeStart = h.total_prize_start || 0;
      const prizeLatest = h.total_prize_latest || 0;
      
      // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
      const earnedPrize = prizeLatest - prizeStart;
      
      // RIO = 落札後に稼いだ賞金総額 / 落札価格
      const rio = soldPrice > 0 ? (earnedPrize * 10000) / soldPrice : 0;
      
      return sum + (isFinite(rio) ? rio : 0);
    }, 0) / horses.length
  ) : 0;
  
  // 平均価格を計算してメタデータを更新
  if (data.metadata) {
    const validPrices = horses
      .map(h => {
        // 価格が数値でない場合は0として扱う
        const price = h.sold_price;
        
        // null, undefined, 空文字の場合はスキップ
        if (price === null || price === undefined) {
          return null;
        }
        
        // 数値の場合はそのまま返す
        if (typeof price === 'number') {
          return price > 0 ? price : null;
        }
        
        // 文字列の場合は数値に変換を試みる
        const strPrice = String(price).trim();
        if (!strPrice) return null;
        
        const num = parseInt(strPrice.replace(/[^0-9]/g, ''), 10);
        return isNaN(num) || num <= 0 ? null : num;
      })
      .filter((price): price is number => 
        price !== null && price > 0
      );
      
    if (validPrices.length > 0) {
      const sum = validPrices.reduce((a, b) => a + b, 0);
      const avg = Math.round(sum / validPrices.length);
      data.metadata.average_price = avg;
    } else {
      data.metadata.average_price = 0;
      console.warn('有効な落札価格データが見つかりませんでした');
    }
  }

  // 指標ボタン用データ
  const roiRanking = [...horses]
    .filter(h => {
      const soldPrice = h.sold_price !== null && h.sold_price !== undefined ? 
        (typeof h.sold_price === 'number' ? h.sold_price : 0) : 0;
      return soldPrice > 0 && h.total_prize_latest;
    })
    .sort((a, b) => {
      const aSoldPrice = a.sold_price !== null && a.sold_price !== undefined ? 
        (typeof a.sold_price === 'number' ? a.sold_price : 0) : 0;
      const bSoldPrice = b.sold_price !== null && b.sold_price !== undefined ? 
        (typeof b.sold_price === 'number' ? b.sold_price : 0) : 0;
      const aROI = a.total_prize_latest ? a.total_prize_latest / (aSoldPrice || 1) : 0;
      const bROI = b.total_prize_latest ? b.total_prize_latest / (bSoldPrice || 1) : 0;
      return bROI - aROI;
    })
    .slice(0, 10);

  const valueHorses = horses.filter(h => {
    const soldPrice = h.sold_price !== null && h.sold_price !== undefined ? 
      (typeof h.sold_price === 'number' ? h.sold_price : 0) : 0;
    const prizeStart = h.total_prize_start || 0;
    const prizeLatest = h.total_prize_latest || 0;
    const earnedPrize = prizeLatest - prizeStart;
    const rio = soldPrice > 0 ? earnedPrize / soldPrice : 0;
    return soldPrice > 0 && rio > avgRIO && soldPrice < (data.metadata?.average_price || 0);
  });

  // 表示切替
  let tableHorses: HorseWithAuction[] = [...horses];
  if (showType === 'roi') tableHorses = [...roiRanking];
  if (showType === 'value') tableHorses = [...valueHorses];

  // 年齢を表示するヘルパー関数（null/undefined/空文字の場合は'-'を表示）
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return `${age}歳`;
  };

  // 落札価格を表示するヘルパー関数
  const displayPrice = (price: number | string | null | undefined, isUnsold: boolean = false): string => {
    return normalize.formatSoldPrice(price, isUnsold);
  };

  // 賞金を表示するヘルパー関数
  const displayPrize = (prize: number | string | null | undefined): string => {
    return normalize.formatPrize(prize);
  };

  // ROIを計算するヘルパー関数
  const calcROI = (prizeLatest: number | undefined, prizeStart: number | undefined, price: number | string | null | undefined): string => {
    if (prizeLatest === undefined || prizeStart === undefined || !price) return '-';
    const numPrice = typeof price === 'string' ? parseFloat(price) : price;
    if (isNaN(numPrice) || numPrice <= 0) return '-';
    
    // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
    const earnedPrize = prizeLatest - prizeStart;
    
    // 落札価格が0以下の場合は計算不可
    if (numPrice <= 0) return '-';
    
    // RIO = 落札後に稼いだ賞金総額 / 落札価格
    const rio = (earnedPrize * 10000) / numPrice;
    
    // パーセンテージで返す（例: 0.15 → 15.0%）
    return (rio * 100).toFixed(1) + '%';
  };

  // ソート関数の型定義
  type SortFunction = (a: HorseWithAuction, b: HorseWithAuction) => number;
  const sortFunctions: Record<string, SortFunction> = {
    name: (a, b) => (a.name || '').localeCompare(b.name || '', 'ja'),
    sex: (a, b) => (a.sex || '').localeCompare(b.sex || '', 'ja'),
    weight: (a, b) => (a.weight || 0) - (b.weight || 0),
    age: (a, b) => {
      const ageA = typeof a.age === 'number' ? a.age : parseFloat(a.age as string) || 0;
      const ageB = typeof b.age === 'number' ? b.age : parseFloat(b.age as string) || 0;
      return ageA - ageB;
    },
    sire: (a, b) => (a.sire || '').localeCompare(b.sire || '', 'ja'),
    sold_price: (a, b) => {
      const aPrice = a.sold_price !== null && a.sold_price !== undefined ? 
        (typeof a.sold_price === 'number' ? a.sold_price : 0) : 0;
      const bPrice = b.sold_price !== null && b.sold_price !== undefined ? 
        (typeof b.sold_price === 'number' ? b.sold_price : 0) : 0;
      return aPrice - bPrice;
    },
    total_prize_start: (a, b) => (a.total_prize_start || 0) - (b.total_prize_start || 0),
    total_prize_latest: (a, b) => (a.total_prize_latest || 0) - (b.total_prize_latest || 0),
    roi: (a, b) => {
      const aSoldPrice = typeof a.sold_price === 'number' ? a.sold_price : 0;
      const bSoldPrice = typeof b.sold_price === 'number' ? b.sold_price : 0;
      
      // 落札後に稼いだ賞金総額 = 現在の総賞金 - オークション時の総賞金
      const aEarnedPrize = (a.total_prize_latest || 0) - (a.total_prize_start || 0);
      const bEarnedPrize = (b.total_prize_latest || 0) - (b.total_prize_start || 0);
      
      // RIO = 落札後に稼いだ賞金総額 / 落札価格
      const aROI = aSoldPrice > 0 ? aEarnedPrize / aSoldPrice : 0;
      const bROI = bSoldPrice > 0 ? bEarnedPrize / bSoldPrice : 0;
      
      return aROI - bROI;
    },
  };

  if (sortKey && sortFunctions[sortKey]) {
    tableHorses = [...tableHorses].sort((a, b) => {
      const res = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? res : -res;
    });
  }

  // ソートハンドラ
  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder(key === 'name' ? 'asc' : 'desc');
    }
  };

  // ソートアイコン
  const renderSortIcon = (key: string) => {
    if (sortKey !== key) return <FaSort className="inline ml-1 text-gray-400" />;
    return sortOrder === 'asc' ? <FaSortUp className="inline ml-1 text-blue-600" /> : <FaSortDown className="inline ml-1 text-blue-600" />;
  };

  // 詳細ページのURLを安全に取得するヘルパー関数
  const getDetailUrl = (horse: HorseWithAuction): string | undefined => {
    return horse.detail_url || undefined;
  };

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-7xl mx-auto">
        {/* サマリー 横並びテキスト */}
        <div className="mb-6 text-lg font-semibold text-gray-700 flex flex-wrap gap-8">
          <span>総馬数: {horses.length}</span>
          <span>平均落札価格: {normalize.formatCurrency(data.metadata.average_price)}</span>
          <span>平均ROI: {avgRIO.toFixed(2)}%</span>
        </div>
        {/* 指標ボタン（白文字色付き） */}
        <div className="flex gap-4 mb-6">
          <Button onClick={() => setShowType('all')} variant="default" className={showType==='all'?"bg-blue-600 text-white":"bg-blue-400 text-white"}>全馬</Button>
          <Button onClick={() => setShowType('roi')} variant="default" className={showType==='roi'?"bg-green-600 text-white":"bg-green-400 text-white"}>ROIランキング</Button>
          <Button onClick={() => setShowType('value')} variant="default" className={showType==='value'?"bg-orange-600 text-white":"bg-orange-400 text-white"}>妙味馬</Button>
        </div>
        {/* DataTable風の表 */}
        <div className="overflow-x-auto bg-white rounded-lg shadow w-full">
          <table className="min-w-full divide-y divide-gray-200 w-full">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('name')}>馬名{renderSortIcon('name')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sex')}>性別{renderSortIcon('sex')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('age')}>年齢{renderSortIcon('age')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sire')}>父{renderSortIcon('sire')}</th>
                <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('weight')}>馬体重 (kg){renderSortIcon('weight')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sold_price')}>落札価格{renderSortIcon('sold_price')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_start')}>オークション時賞金{renderSortIcon('total_prize_start')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_latest')}>現在賞金{renderSortIcon('total_prize_latest')}</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('roi')}>ROI{renderSortIcon('roi')}</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">リンク</th>
                <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24">病歴</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tableHorses.map((horse) => (
                <tr key={horse.id} className="hover:bg-blue-50">
                  <td className="px-3 py-2 font-medium text-gray-900 whitespace-nowrap">
                    <Link href={`/horses/${horse.id}`} className="hover:underline text-blue-700 whitespace-nowrap">{horse.name}</Link>
                  </td>
                  <td className="px-3 py-2">
                    {(() => {
                      const sexInfo = normalize.formatSex(horse.sex);
                      return (
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium text-white ${sexInfo.color}`}>
                          {sexInfo.icon} {sexInfo.text}
                        </span>
                      );
                    })()}
                  </td>
                  <td className="px-3 py-2">{displayAge(horse.age)}</td>
                  <td className="px-3 py-2">{horse.sire || '-'}</td>
                  <td className="px-3 py-2 text-right">{horse.weight ? `${horse.weight} kg` : '-'}</td>
                  <td className="px-3 py-2">
                    {displayPrice(horse.sold_price, horse.is_unsold)}
                  </td>
                  <td className="px-3 py-2">{displayPrize(horse.total_prize_start)}</td>
                  <td className="px-3 py-2">{displayPrize(horse.total_prize_latest)}</td>
                  <td className="px-3 py-2">
                    {calcROI(horse.total_prize_latest, horse.total_prize_start, horse.sold_price)}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1 items-center">
                      {horse.jbis_url && (
                        <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline whitespace-nowrap">JBIS</a>
                      )}
                      {getDetailUrl(horse) && (
                        <a href={getDetailUrl(horse)} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline whitespace-nowrap">サラオク</a>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {(() => {
                      // 病歴が「なし」の馬を判定
                      const isNoDisease = (tags: any) => {
                        if (tags === undefined || tags === null || tags === '') return true;
                        if (Array.isArray(tags)) {
                          if (tags.length === 0) return true;
                          return tags.every(tag => {
                            const strTag = String(tag).trim();
                            return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
                          });
                        }
                        const strTag = String(tags).trim();
                        return strTag === '' || strTag === '-' || strTag === 'なし' || strTag === 'なし。' || strTag === '特になし' || strTag === '特になし。';
                      };
                      
                      // 病歴が「なし」の場合は青で表示、それ以外はピンクで「あり」と表示
                      return isNoDisease(horse.disease_tags) ? (
                        <span className="text-xs font-medium bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">
                          なし
                        </span>
                      ) : (
                        <span className="text-xs font-medium bg-pink-100 text-pink-800 px-2 py-0.5 rounded-full whitespace-nowrap inline-block w-12">
                          あり
                        </span>
                      );
                    })()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
