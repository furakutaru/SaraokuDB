'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { Horse, ImageUrl, HorseData, AuctionHistory, HorseWithCalculations } from '@/types/horse';
import { useCallback, useEffect, useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { getDisplayPrice } from '@/utils/price';
import { formatWeight, formatPrizeFromYen } from '@/utils/format';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { normalizeImageUrl } from '@/utils/url';

// 共有型に、このコンポーネント固有のフィールドを追加
// BaseHorseWithCalculations & { effectiveAuction: AuctionHistory }はBaseHorseWithCalculationsを拡張

interface AnalysisData {
  horses: HorseWithCalculations[];
  metadata: {
    last_updated: string;
    total_horses: number;
    average_price: number;
    average_growth_rate: number | string;
    horses_with_growth_data: number;
  };
}

type ShowType = 'all' | 'sold' | 'unsold' | 'roi' | 'value';

// 馬データを変換する関数
const transformHorseData = (horses: any[]): HorseWithCalculations[] => {
  // 明示的に型を指定した空配列を定義
  const emptyResult: HorseWithCalculations[] = [];
  if (!horses || !Array.isArray(horses)) return emptyResult;
  
  return horses.filter(horse => horse !== null).map((horse, index) => {
    const horseId = horse.id || `horse-${Date.now()}`;
    
    // オークション履歴を取得（historyまたはauction_historyのいずれかを使用）
    const auctionHistory = Array.isArray(horse.history) 
      ? horse.history 
      : Array.isArray(horse.auction_history) 
        ? horse.auction_history 
        : [];
    
    // 馬体重を取得するヘルパー関数
    const getEffectiveWeight = (): number => {
      // 馬オブジェクトの体重を確認
      if (horse.weight !== undefined && horse.weight !== null) {
        const weight = Number(horse.weight);
        return isNaN(weight) ? 0 : weight;
      }
      
      // オークション履歴から最新の体重を確認
      if (auctionHistory.length > 0) {
        const validAuction = auctionHistory.find((auction: any) => 
          auction.weight !== undefined && 
          auction.weight !== null && 
          Number(auction.weight) > 0
        );
        if (validAuction) {
          return Number(validAuction.weight);
        }
      }
      
      return 0;
    };
    
    const horseWeight = getEffectiveWeight();
    
    // オークション情報を初期化
    const initAuction = (): AuctionHistory => ({
      id: horse.auction_id || `auction-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      horse_id: horseId,
      auction_date: horse.auction_date || new Date().toISOString(),
      sold_price: horse.sold_price || null,
      total_prize_start: 0,
      total_prize_latest: 0,
      weight: horseWeight || 0,
      seller: '',
      is_unsold: false,
      unsold: false,
      comment: '',
      created_at: new Date().toISOString(),
      detail_url: horse.auction_url || '',
      auction_url: horse.auction_url || ''
    });

    // 最新のオークション情報を取得（なければ新規作成）
    const latestAuction = auctionHistory.length > 0 ? auctionHistory[0] : initAuction();

    // 有効なオークション情報を作成
    const effectiveAuction: AuctionHistory = {
      ...latestAuction,
      auction_date: latestAuction.auction_date || horse.auction_date || new Date().toISOString(),
      sold_price: horse.sold_price !== undefined ? horse.sold_price : latestAuction.sold_price,
      weight: horseWeight || latestAuction.weight || 0,
      seller: horse.seller || latestAuction.seller || ''
    };

    // 販売価格を取得（馬オブジェクト直下のsold_priceを優先）
    // 馬オブジェクトにsold_priceがなく、オークション履歴にsold_priceがある場合はそれを使用
    // どちらにも値がない場合はnullを設定
    let soldPrice: number | null = null;
    let priceSource: string = 'none';
    
    // 馬体重を表示用にフォーマット
    const displayWeight = horseWeight !== null ? `${horseWeight}kg` : '不明';
    
    // 1. 馬オブジェクトのsold_priceを確認
    if (horse.sold_price !== undefined && horse.sold_price !== null) {
      const price = Number(horse.sold_price);
      if (!isNaN(price)) {
        soldPrice = price;
        priceSource = 'horse';
      }
    } 
    // 2. オークション履歴のsold_priceを確認
    if ((soldPrice === null || soldPrice === 0) && latestAuction.sold_price !== undefined && latestAuction.sold_price !== null) {
      const price = Number(latestAuction.sold_price);
      if (!isNaN(price)) {
        soldPrice = price;
        priceSource = 'auction';
      }
    }
    
    console.log(`[${index}] ${horse.name} - soldPrice:`, {
      value: soldPrice,
      source: priceSource,
      horse_sold_price: horse.sold_price,
      auction_sold_price: latestAuction.sold_price
    });
    
    // 主取りの判定: 
    // 1. 明示的にis_unsoldまたはunsoldフラグが立っているとき
    // 2. オークションが終了していて、sold_priceがnullまたは0の場合
    const auctionEndDate = latestAuction?.auction_date ? new Date(latestAuction.auction_date) : null;
    const isAuctionEnded = auctionEndDate ? auctionEndDate < new Date() : false;
    
    const hasUnsoldFlag = 
      horse.is_unsold === true || 
      horse.unsold === true ||
      (latestAuction && (latestAuction.is_unsold === true || latestAuction.unsold === true));
    
    const isHorseUnsold = hasUnsoldFlag || 
      (isAuctionEnded && (soldPrice === null || soldPrice <= 0));
    
    console.log(`[${index}] ${horse.name} - isHorseUnsold:`, isHorseUnsold, {
      horse_unsold: horse.unsold,
      horse_is_unsold: horse.is_unsold,
      latestAuction_unsold: latestAuction?.unsold,
      latestAuction_is_unsold: latestAuction?.is_unsold,
      soldPrice,
      priceSource,
      auction_ended: isAuctionEnded,
      auction_end_date: auctionEndDate?.toISOString(),
      hasUnsoldFlag,
      decision: isHorseUnsold ? 'unsold' : 'sold'
    });
    
    // 馬体重を適切に取得（馬オブジェクトまたはオークション履歴から）
    const effectiveWeight = (() => {
      // 馬オブジェクトの体重を取得
      const horseWeight = horse.weight !== undefined && horse.weight !== null 
        ? Number(horse.weight)
        : null;
      
      // オークション履歴の体重を取得
      const auctionWeight = latestAuction && latestAuction.weight !== undefined && latestAuction.weight !== null 
        ? Number(latestAuction.weight)
        : null;
      
      // デバッグ用ログ
      console.log(`[${index}] ${horse.name} - weights:`, {
        horseWeight,
        auctionWeight,
        horse_weight: horse.weight,
        auction_weight: latestAuction?.weight,
        horse: JSON.stringify(horse, null, 2), // 馬オブジェクト全体を出力
        latestAuction: latestAuction ? JSON.stringify(latestAuction, null, 2) : 'No latestAuction',
        horseRaw: horse,
        latestAuctionRaw: latestAuction
      });
      
      // 有効な体重を返す（0より大きい値のみ有効）
      const result = (horseWeight !== null && horseWeight > 0) ? horseWeight :
                   (auctionWeight !== null && auctionWeight > 0) ? auctionWeight :
                   null;
      
      console.log(`[${index}] ${horse.name} - effectiveWeight:`, result);
      return result;
    })();
    
    // 馬の基本情報と最新のオークション情報をマージ
    // 馬オブジェクト直下の情報を優先し、なければオークション履歴の情報を使用
    const horseWithDetails: HorseWithCalculations & { effectiveAuction: AuctionHistory } = {
      // 必須フィールドを設定
      id: horseId,
      name: horse.name || '不明',
      age: typeof horse.age === 'number' ? horse.age : (parseInt(horse.age, 10) || 0),
      sex: horse.sex || '不明',
      sire: horse.sire || '不明',
      dam: horse.dam || '不明',
      damsire: horse.damsire || '不明',
      image_url: horse.image_url,
      jbis_url: horse.jbis_url || '',
      auction_url: horse.auction_url || '',
      detail_url: horse.detail_url || horse.auction_url || `#/horse/${horseId}`,
      disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags : [],
      created_at: horse.created_at || new Date().toISOString(),
      updated_at: horse.updated_at || new Date().toISOString(),
      // オークション関連情報
      auction_date: horse.auction_date || latestAuction.auction_date || '',
      sold_price: soldPrice,
      seller: horse.seller || latestAuction.seller || '',
      weight: effectiveWeight,
      total_prize_start: horse.total_prize_start || latestAuction.total_prize_start || 0,
      total_prize_latest: horse.total_prize_latest || latestAuction.total_prize_latest || 0,
      // 主取り（unsold）の判定
      unsold: isHorseUnsold,
      unsold_count: auctionHistory.filter((a: any) => a.sold_price === null || a.sold_price === 0).length,
      comment: horse.comment || '',
      // 計算フィールド
      roi: 0,
      price_per_kg: 0,
      display_price: '',  // 後で設定
      display_weight: displayWeight,
      display_prize: '',
      // ソート用の仮想フィールド
      sort_price: soldPrice || 0,
      sort_prize: horse.total_prize_latest || 0,
      sort_roi: 0,
      // Horse インターフェースの必須フィールド
      sire: horse.sire || '',
      dam: horse.dam || '',
      damsire: horse.damsire || '',
      image_url: horse.image_url || { image_url: '' },
      primary_image: normalizeImageUrl(horse.image_url),
      detail_url: horse.auction_url || `#/horse/${horseId}`,
      auction_history: auctionHistory,
      // その他の必須フィールド
      is_auction: false,
      is_new: false,
      is_updated: false,
      is_featured: false,
      is_sold: false,
      is_unsold: isHorseUnsold,
      is_withdrawn: false,
      is_reserved: false,
      is_favorite: false,
      is_watchlist: false,
      is_compare: false,
      is_selected: false,
      is_loading: false,
      is_error: false,
      error_message: '',
      effectiveAuction: effectiveAuction
    };

    // 主取り理由を記録
    const unsoldReasons = {
      // 価格関連の理由
      soldPriceNull: soldPrice === null,
      soldPriceZero: soldPrice === 0,
      soldPriceUndefined: soldPrice === undefined,
      
      // 馬オブジェクトのフラグ
      horseIsUnsold: horse.is_unsold === true,
      horseUnsold: horse.unsold === true,
      
      // オークション履歴のフラグ
      auctionIsUnsold: latestAuction.is_unsold === true,
      auctionUnsold: latestAuction.unsold === true,
      
      // オークション状態
      isAuctionEnded,
      auctionDate: latestAuction.auction_date,
      
      // 販売価格情報
      horseSoldPrice: horse.sold_price,
      auctionSoldPrice: latestAuction.sold_price
    };

    // 主取り判定をより正確に行う
    // 1. 明示的にunsoldフラグが立っていいる場合は主取りと判定
    // 2. 販売価格がnullの場合は主取りと判定
    const isUnsold = 
      horse.is_unsold === true ||
      horse.unsold === true ||
      latestAuction.is_unsold === true ||
      latestAuction.unsold === true ||
      soldPrice === null;  // soldPriceが0の場合は主取りと判定しない
    
    // デバッグ用に主取り理由を記録（最初の5頭のみ）
    if (index < 5) {
      const decisionReasons = [];
      if (horse.is_unsold === true) decisionReasons.push('馬オブジェクトのis_unsoldフラグがtrue');
      if (horse.unsold === true) decisionReasons.push('馬オブジェクトのunsoldフラグがtrue');
      if (latestAuction.is_unsold === true) decisionReasons.push('オークション履歴のis_unsoldフラグがtrue');
      if (latestAuction.unsold === true) decisionReasons.push('オークション履歴のunsoldフラグがtrue');
      if (soldPrice === 0) decisionReasons.push('販売価格が0のため主取りと判定');
      if (soldPrice === null) decisionReasons.push('販売価格が未設定');
      
      console.groupCollapsed(`[${index}] ${horse.name} - ${isHorseUnsold ? '主取り' : '落札'}`);
      console.log('主取り判定の根拠:', decisionReasons.length > 0 ? decisionReasons.join('、') : '主取りの根拠なし（落札済み）');
      console.log('販売価格情報:', { 
        soldPrice,
        horseSoldPrice: horse.sold_price,
        auctionSoldPrice: latestAuction.sold_price,
        isAuctionEnded,
        auctionDate: latestAuction.auction_date,
        unsoldReasons: {
          soldPriceNull: latestAuction.sold_price === null,
          soldPriceZero: latestAuction.sold_price === 0,
          soldPriceUndefined: latestAuction.sold_price === undefined,
          isUnsoldFlag: latestAuction.is_unsold === true,
          unsoldFlag: latestAuction.unsold === true
        }
      });
      console.log('フラグ状態:', {
        horse: {
          is_unsold: horse.is_unsold,
          unsold: horse.unsold
        },
        latestAuction: {
          is_unsold: latestAuction.is_unsold,
          unsold: latestAuction.unsold
        }
      });
      console.log('詳細情報:', {
        horseId: horse.id,
        name: horse.name,
        auctionDate: latestAuction.auction_date || horse.auction_date,
        weight: effectiveWeight !== null ? effectiveWeight : '不明',
        comment: horse.comment ? (horse.comment.length > 50 ? horse.comment.substring(0, 50) + '...' : horse.comment) : 'コメントなし',
        isUnsold
      });
      console.groupEnd();
    }
                    
    const weight = effectiveWeight ?? 0;
    
    // 賞金情報を取得（prize_money.total_prize または latestAuction.total_prize_latest から取得）
    let prizeMoney = 0;
    if (horse.prize_money?.total_prize) {
      // 例: "2,000,000円" から数値に変換
      const prizeStr = horse.prize_money.total_prize.replace(/[^0-9]/g, '');
      prizeMoney = parseInt(prizeStr, 10) || 0;
    } else {
      prizeMoney = latestAuction.total_prize_latest ?? 0;
    }
    
    const numericSoldPrice = typeof soldPrice === 'string' ? parseFloat(soldPrice) || 0 : soldPrice || 0;
    const numericPrizeMoney = typeof prizeMoney === 'string' ? parseFloat(prizeMoney) || 0 : prizeMoney || 0;
    
    // ROI計算（落札価格が0の場合は0）
    const roi = numericSoldPrice > 0 ? (numericPrizeMoney / numericSoldPrice) * 100 : 0;
    
    // 画像URLの正規化
    let imageUrl = '';
    if (typeof horse.image_url === 'object' && horse.image_url !== null) {
      imageUrl = (horse.image_url as ImageUrl).image_url || '';
    } else if (typeof horse.image_url === 'string') {
      imageUrl = horse.image_url || '';
    }
    
    // 基本情報を設定
    // 画像URLを正規化
    const normalizedImageUrl = normalizeImageUrl(horse.image_url);
    
    const baseHorse: HorseWithCalculations = {
      // 必須フィールドを設定
      id: horseId,
      name: horse.name || '不明',
      age: typeof horse.age === 'number' ? horse.age : (parseInt(horse.age, 10) || 0),
      sex: horse.sex || '不明',
      sire: horse.sire || '不明',
      dam: horse.dam || '不明',
      damsire: horse.damsire || '不明',
      image_url: horse.image_url,
      jbis_url: horse.jbis_url || '',
      auction_url: horse.auction_url || '',
      detail_url: horse.detail_url || horse.auction_url || `#/horse/${horseId}`,
      disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags : [],
      created_at: horse.created_at || new Date().toISOString(),
      updated_at: horse.updated_at || new Date().toISOString(),
      // オークション関連情報
      auction_date: horse.auction_date || latestAuction.auction_date || '',
      sold_price: soldPrice,
      seller: horse.seller || latestAuction.seller || '',
      weight: effectiveWeight,
      total_prize_start: horse.total_prize_start || latestAuction.total_prize_start || 0,
      total_prize_latest: horse.total_prize_latest || latestAuction.total_prize_latest || 0,
      // 主取り（unsold）の判定
      unsold: isUnsold,
      unsold_count: auctionHistory.filter((a: any) => a.sold_price === null || a.sold_price === 0).length,
      comment: horse.comment || ''
    };

    // 表示用の価格を設定
    const displayPriceValue = getDisplayPrice({
      ...baseHorse,
      sold_price: soldPrice,
      unsold: isUnsold,
      history: auctionHistory,
      auction_history: auctionHistory,
      effectiveAuction: effectiveAuction,
      price_per_kg: 0,
      roi: 0,
      display_price: '',
      display_weight: '',
      display_prize: '',
      sort_roi: 0,
      sort_prize: 0,
      sort_price: 0,
      primary_image: '',
      is_auction: true,
      is_sold: false,
      is_unsold: isUnsold,
      unsold_count: isUnsold ? 1 : 0,
      total_prize_start: 0,
      total_prize_latest: 0
    });

    // 表示用の馬データを返す
    const effectiveWeightNum = effectiveWeight || 0; // nullの場合は0を使用
    const pricePerKg = effectiveWeightNum > 0 && numericSoldPrice > 0 
      ? numericSoldPrice / effectiveWeightNum 
      : 0;

    // 馬データを構築
    const horseData: HorseWithCalculations = {
      // 基本情報
      ...baseHorse,
      
      // 計算済みの値
      price_per_kg: pricePerKg,
      roi: roi,
      display_price: displayPriceValue,
      display_weight: effectiveWeightNum > 0 ? `${effectiveWeightNum}kg` : '-',
      display_prize: numericPrizeMoney > 0 ? `¥${numericPrizeMoney.toLocaleString()}` : '-',
      display_roi: roi > 0 ? `${roi.toFixed(1)}x` : 'N/A',
      
      // ソート用の値
      sort_roi: roi,
      sort_prize: numericPrizeMoney,
      sort_price: numericSoldPrice,
      
      // 画像関連
      primary_image: normalizedImageUrl,
      
      // オークション情報
      effectiveAuction: latestAuction,
      history: auctionHistory,
      auction_history: auctionHistory,
      
      // 状態フラグ
      is_sold: !isUnsold && numericSoldPrice > 0,
      is_unsold: isUnsold,
      
      // デフォルトフラグ
      is_new: false,
      is_updated: false,
      is_featured: false,
      is_withdrawn: false,
      is_reserved: false,
      is_favorite: false,
      is_watchlist: false,
      is_compare: false,
      is_selected: false,
      is_loading: false,
      is_error: false,
      error_message: '',
      
      // その他の必須プロパティ
      is_auction: true,
      unsold_count: isUnsold ? 1 : 0,
      total_prize_start: latestAuction?.total_prize_start || 0,
      total_prize_latest: latestAuction?.total_prize_latest || 0
    };

    return horseData;

// ...

const formatDisplayPrice = (price: number | string | null | undefined, horse: HorseWithCalculations): string => {
  // 明示的に主取りフラグが立っているときは「主取り」を返す
  const isUnsold = horse.is_unsold === true || 
                  horse.unsold === true || 
                  (horse.effectiveAuction && (horse.effectiveAuction.is_unsold === true || horse.effectiveAuction.unsold === true));
  
  if (isUnsold) {
    return '主取り';
  }
  
  // 価格がnullまたはundefinedの場合は「-」を返す
  if (price === null || price === undefined) {
    return '-';
  }

  // 価格が0の場合は0円と表示
  if (price === 0 || price === '0') {
    return formatPrice(0);
  }

  // それ以外の場合はフォーマットして返す
  return getDisplayPrice(price);
};

// ...

// ソート処理の適用
console.log('フィルタリング後の馬データ:', tableHorses);
if (sortKey && sortFunctions[sortKey]) {
  tableHorses = [...tableHorses].sort((a, b) => {
    const result = sortFunctions[sortKey](a, b);
    return sortOrder === 'asc' ? result : -result;
  });
  console.log('ソート後の馬データ:', tableHorses);
}

// ...
    const result = sortFunctions[sortKey](a, b);
    return sortOrder === 'asc' ? result : -result;
  });
  console.log('ソート後の馬データ:', tableHorses);
  
  // 詳細ページURLを取得するヘルパー関数
  const getDetailUrl = (horse: HorseWithCalculations): string => {
    return horse.detail_url || '';
  };

  console.log('レンダリング時の馬データ:', tableHorses);

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="mb-4 p-4 bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700">
          <p>デバッグ情報: 表示中の馬の数: {tableHorses.length}</p>
          <p>表示タイプ: {showType}</p>
          <p>フィルター: 性別={filterBySex}, 年齢={filterByAge}, 父馬={filterBySire}, 母馬={filterByDam}</p>
        </div>
      {/* サマリー 横並びテキスト */}
      <div className="mb-6 text-lg font-semibold text-gray-700 flex flex-wrap gap-8">
        <span>総馬数: {tableHorses.length}</span>
        <span>平均落札価格: {formatPrice(data.metadata.average_price)}</span>
        <span>平均ROI: {avgROI.toFixed(2)}</span>
      </div>
      {/* 指標ボタン（白文字色付き） */}
      <div className="flex gap-4 mb-6">
        <Button onClick={() => setShowType('all')} variant="default" className={showType==='all'?"bg-blue-600 text-white":"bg-blue-400 text-white"}>全馬</Button>
        <Button onClick={() => setShowType('roi')} variant="default" className={showType==='roi'?"bg-green-600 text-white":"bg-green-400 text-white"}>ROIランキング</Button>
        <Button onClick={() => setShowType('value')} variant="default" className={showType==='value'?"bg-orange-600 text-white":"bg-orange-400 text-white"}>妙味馬</Button>
      </div>
      {/* DataTable風の表 */}
      <div className="overflow-x-auto bg-white rounded-lg shadow">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-100">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('name')}>馬名{renderSortIcon('name', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sex')}>性別{renderSortIcon('sex', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('age')}>年齢{renderSortIcon('age', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sire')}>父{renderSortIcon('sire', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-right text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('weight')}>馬体重 (kg){renderSortIcon('weight', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('sold_price')}>落札価格{renderSortIcon('sold_price', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_start')}>オークション時賞金{renderSortIcon('total_prize_start', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('total_prize_latest')}>現在賞金{renderSortIcon('total_prize_latest', sortKey, sortOrder)}</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase cursor-pointer" onClick={() => handleSort('roi')}>ROI{renderSortIcon('roi', sortKey, sortOrder)}</th>
              <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase">リンク</th>
              <th className="px-2 py-2 text-center text-xs font-medium text-gray-500 uppercase w-24">病歴</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {tableHorses.map((horse, index) => (
              <tr 
                key={`${horse.id || 'horse'}-${index}`} 
                className="hover:bg-blue-50"
              >
                <td className="px-3 py-2 font-medium text-gray-900">
                  <Link href={`/horses/${String((horse as any).auction_id || horse.id)}`} className="hover:underline text-blue-700">{horse.name}</Link>
                </td>
                <td className="px-3 py-2">{horse.sex}</td>
                <td className="px-3 py-2">{displayAge(horse.age)}</td>
                <td className="px-3 py-2">{horse.sire}</td>
                <td className="px-3 py-2 text-right">{formatWeight(horse.weight)}</td>
                <td className="px-3 py-2">
                  {horse.display_price}
                </td>
                <td className="px-3 py-2">-</td>
                <td className="px-3 py-2">
                  {horse.prize_money ? formatPrizeFromYen(horse.prize_money.total_prize) : '-'}
                </td>
                <td className="px-3 py-2">
                  {horse.prize_money ? 
                    calcROI(horse.prize_money.total_prize, horse.sold_price ?? undefined) : 
                    calcROI(undefined, horse.sold_price ?? undefined)}
                </td>
                <td className="px-3 py-2">
                  <div className="flex flex-col gap-1 items-center">
                    {horse.jbis_url && (
                      <a 
                        href={horse.jbis_url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-xs text-blue-600 hover:text-blue-800 underline whitespace-nowrap"
                        title="JBISで詳細を確認"
                      >
                        JBIS
                      </a>
                    )}
                    {horse.auction_url && (
                      <a 
                        href={horse.auction_url} 
                        target="_blank" 
                        rel="noopener noreferrer" 
                        className="text-xs text-green-600 hover:text-green-800 underline whitespace-nowrap"
                        title="オークションページで詳細を確認"
                      >
                        サラオク
                      </a>
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
