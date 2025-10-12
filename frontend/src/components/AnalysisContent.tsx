'use client';

import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { 
  AuctionHistory, 
  BaseHorse, 
  HorseData, 
  Metadata, 
  PrizeMoney, 
  ImageUrl 
} from '../types/horse';
import { useState, useMemo, useEffect, useCallback } from 'react';
import { format, format as dateFnsFormat } from 'date-fns';
import { ja } from 'date-fns/locale';
import { formatPrice, getDisplayPrice } from '../utils/price';
import { FaSort, FaSortUp, FaSortDown } from 'react-icons/fa';
import { normalizeImageUrl } from '../utils/url';

// 表示タイプの型
type ShowType = 'all' | 'sold' | 'unsold' | 'roi' | 'value';

// 分析データの型
interface AnalysisData {
  horses: AnalysisHorse[];
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

// 分析用の馬情報の型
interface AnalysisHorse extends BaseHorse {
  id: string | number;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  weight?: number | null;
  primary_image: string;
  jbis_url?: string;
  detail_url?: string;
  rakuten_url?: string;
  auction_url?: string;
  disease_tags?: string[];
  unsold_count?: number;
  is_unsold?: boolean;
  unsold?: boolean;
  comment?: string;
  effectiveAuction: AuctionHistory;
  sold_price?: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  auction_history?: AuctionHistory[];
  prize_money?: PrizeMoney;
  display_weight?: string;
  display_price?: string;
  sort_price?: number;
  sort_prize?: number;
  sort_roi?: number;
  roi?: number;
  price_per_kg?: number;
  effectiveWeight?: number | null;
}

// 馬体重をフォーマットする関数（整数値のみを想定）
function formatWeight(weight: number | string | null | undefined): string {
  console.log('formatWeight called with:', weight, 'type:', typeof weight);
  if (weight === null || weight === undefined || weight === '') {
    return '-';
  }
  // 数値に変換して整数に丸める
  const num = typeof weight === 'string' ? parseInt(weight, 10) : Math.floor(Number(weight));
  console.log('formatted weight:', num);
  return isNaN(num) ? '-' : `${num}kg`;
}

// 表示用の拡張型
interface HorseWithCalculations extends AnalysisHorse {
  display_weight: string;
  display_price: string;
  display_prize: string;
  display_roi: string;
  sort_price: number;
  sort_prize: number;
  sort_roi: number;
  roi?: number;
  price_per_kg?: number;
  
  // 賞金情報
  prize_money?: {
    total_prize: string;
  };
  
  // 疾患タグ
  disease_tags?: string[];
  
  // 画像関連
  primary_image: string;
  
  // 外部リンク
  jbis_url?: string;
  detail_url?: string;  // 楽天競馬の詳細ページURL
  rakuten_url?: string; // 楽天競馬のURL（detail_urlと同一の可能性あり）
  auction_url?: string; // オークションURL（存在しない場合はdetail_urlを使用）
  
  // 表示用プロパティ（BaseHorseWithCalculations から継承）
  // display_weight: string;
  // display_prize: string;
  // display_roi: string;
  // sort_price: number;
  // sort_prize: number;
  // sort_roi: number;
}

interface AnalysisData {
  horses: AnalysisHorse[];
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

// 馬データを変換する関数
const transformHorseData = (data: any): AnalysisHorse[] => {
  console.log('=== transformHorseData called ===');
  console.log('Input data:', data);
  
  // データ構造の検証
  if (!data || typeof data !== 'object') {
    console.error('Invalid data format: Expected an object', data);
    return [];
  }
  
  // 馬データの配列を取得
  const horsesArray = Array.isArray(data) ? data : 
                     (data.horses && Array.isArray(data.horses) ? data.horses : []);
  
  // メタデータを保持
  const metadata = {
    last_updated: data.last_updated || new Date().toISOString(),
    total_horses: data.total_horses || 0,
    average_price: data.average_price || 0,
    average_growth_rate: data.average_growth_rate || 0,
    horses_with_growth_data: data.horses_with_growth_data || 0
  };
  
  console.log(`Transforming ${horsesArray.length} horses`);
  if (horsesArray.length > 0) {
    console.log('First horse keys:', Object.keys(horsesArray[0]));
    console.log('First horse data:', JSON.stringify(horsesArray[0], null, 2));
  }
  
  try {
    console.log('Starting to process horses...');
    
    const validHorses = horsesArray.filter((horse: any) => {
      if (!horse) {
        console.log('Found null or undefined horse, filtering out');
        return false;
      }
      
      console.log(`Processing horse: ${horse.name || 'No name'} (ID: ${horse.id || 'No ID'})`);
      
      if (!horse.id && !horse.name) {
        console.log('Horse missing required fields (id and name):', JSON.stringify(horse, null, 2));
        return false;
      }
      return true;
    });
    
    console.log(`Filtered ${horsesArray.length - validHorses.length} invalid horses`);
    
    const result = validHorses.map((horse: any, index: number): AnalysisHorse => {
      console.log(`[${index}] Mapping horse:`, horse.name || 'No name');
    // IDを明示的に文字列に変換
    const horseId = horse.id ? String(horse.id) : `horse-${Date.now()}`;
    
    // オークション履歴を取得（historyまたはauction_historyのいずれかを使用）
    const auctionHistory = Array.isArray(horse.history) 
      ? horse.history 
      : Array.isArray(horse.auction_history) 
        ? horse.auction_history 
        : [];
    
    // 馬体重を取得するヘルパー関数
    const getEffectiveWeight = (): number | null => {
      // 1. 馬オブジェクトの体重を確認
      if (horse.weight !== undefined && horse.weight !== null && horse.weight !== '') {
        // 数値に変換してチェック
        const weight = Number(horse.weight);
        if (!isNaN(weight) && weight > 0) {
          console.log(`[${index}] ${horse.name} - Using horse.weight:`, weight);
          return Math.floor(weight); // 整数に丸める
        }
      }
      
      // 2. オークション履歴から最新の体重を確認
      if (auctionHistory.length > 0) {
        // 日付でソート（最新が先頭）
        const sortedAuctions = [...auctionHistory].sort((a, b) => 
          new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime()
        );
        
        // 有効な体重を持つ最初のオークションを探す
        const validAuction = sortedAuctions.find(auction => {
          if (auction.weight !== undefined && auction.weight !== null && auction.weight !== '') {
            const weight = Number(auction.weight);
            return !isNaN(weight) && weight > 0;
          }
          return false;
        });
        
        if (validAuction) {
          const weight = Number(validAuction.weight);
          console.log(`[${index}] ${horse.name} - Using auction weight (${validAuction.auction_date}):`, weight);
          return weight;
        }
      }
      console.log(`[${index}] ${horse.name} - No valid weight found`);
      return null;
    };
    
    const horseWeight = getEffectiveWeight();
    const displayWeight = horseWeight !== null ? `${horseWeight}kg` : '不明';
    console.log(`[${index}] ${horse.name} - Final effective weight:`, horseWeight);
    
    // デフォルトのオークションデータ
    const defaultAuction: AuctionHistory = {
      id: horse.auction_id || '',
      horse_id: horseId,
      auction_date: horse.auction_date || '',
      sold_price: horse.sold_price || null,
      total_prize_start: horse.total_prize_start || 0,
      total_prize_latest: horse.total_prize_latest || 0,
      weight: horseWeight,
      seller: '',
      is_unsold: false,
      comment: '',
      created_at: new Date().toISOString(),
      detail_url: '',
      auction_url: ''
    };
    
    // オークション履歴を日付でソート（最新が先頭に来るように）
    const sortedAuctions = [...auctionHistory].sort((a, b) => 
      new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime()
    );
    
    // 最新のオークション情報を取得（なければデフォルト値を使用）
    const latestAuction = sortedAuctions[0] || defaultAuction;
    
    // デバッグ用ログ
    console.log(`[${index}] ${horse.name} - latestAuction:`, {
      id: latestAuction?.id,
      auction_date: latestAuction?.auction_date,
      sold_price: latestAuction?.sold_price,
      weight: latestAuction?.weight
    });
    
    // 販売価格を取得（馬オブジェクト直下のsold_priceを優先）
    // 馬オブジェクトにsold_priceがなく、オークション履歴にsold_priceがある場合はそれを使用
    // どちらにも値がない場合はnullを設定
    let soldPrice: number | null = null;
    let priceSource: string = 'none';
    
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
    // 1. 明示的にis_unsoldまたはunsoldフラグが立っている場合
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
      // デバッグ用に値を確認
      console.log(`[${index}] ${horse.name} - Raw weight values:`, {
        horseWeight: horse.weight,
        horseWeightType: typeof horse.weight,
        latestAuctionWeight: latestAuction?.weight,
        latestAuctionWeightType: typeof latestAuction?.weight
      });

      // 数値に変換するヘルパー関数
      const toNumber = (val: any): number | null => {
        if (val === undefined || val === null) return null;
        const num = Number(val);
        return !isNaN(num) ? num : null;
      };

      // 馬オブジェクトの体重を取得
      const horseWeight = toNumber(horse.weight);
      
      // オークション履歴の体重を取得
      const auctionWeight = latestAuction ? toNumber(latestAuction.weight) : null;
      
      // 有効な体重を返す（0より大きい値のみ有効）
      const result = (horseWeight !== null && horseWeight > 0) 
        ? horseWeight 
        : (auctionWeight !== null && auctionWeight > 0) 
          ? auctionWeight 
          : undefined;
      
      console.log(`[${index}] ${horse.name} - Processed weight:`, {
        horseWeight,
        auctionWeight,
        effectiveWeight: result,
        type: typeof result
      });
      
      return result;
    })();
    
    // 馬の基本情報と最新のオークション情報をマージ
    // 馬オブジェクト直下の情報を優先し、なければオークション履歴の情報を使用
    // デフォルト値で初期化
    const defaultAuctionData = {
      id: horseId,
      horse_id: horseId,
      auction_date: '',
      sold_price: soldPrice,
      total_prize_start: 0,
      total_prize_latest: 0,
      weight: effectiveWeight,
      seller: '',
      is_unsold: isHorseUnsold,
      unsold: isHorseUnsold, // 互換性のため
      comment: '',
      created_at: new Date().toISOString(),
      detail_url: horse.auction_url || '',
      auction_url: horse.auction_url || ''
    };

    // オークション履歴の情報をマージ（最新のものから順に上書き）
    const effectiveAuction: AuctionHistory = {
      ...defaultAuctionData,
      ...(latestAuction || {}),
      // 馬オブジェクト直下の情報で上書き
      id: latestAuction?.id || horseId,
      horse_id: horseId,
      auction_date: horse.auction_date || latestAuction?.auction_date || '',
      sold_price: soldPrice,
      total_prize_start: horse.total_prize_start || latestAuction?.total_prize_start || 0,
      total_prize_latest: horse.total_prize_latest || latestAuction?.total_prize_latest || 0,
      weight: effectiveWeight,
      seller: horse.seller || latestAuction?.seller || '',
      is_unsold: isHorseUnsold,
      unsold: isHorseUnsold,
      comment: horse.comment || latestAuction?.comment || '',
      created_at: latestAuction?.created_at || new Date().toISOString(),
      detail_url: latestAuction?.detail_url || horse.auction_url || '',
      auction_url: latestAuction?.auction_url || horse.auction_url || ''
    };
    
    console.log(`[${index}] ${horse.name} - effectiveAuction:`, {
      sold_price: effectiveAuction.sold_price,
      is_unsold: effectiveAuction.is_unsold,
      unsold: effectiveAuction.unsold
    });
    
    // 主取りの理由を記録
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
                    
    // 体重を取得（undefinedの場合は0を返す）
    const weight = effectiveWeight !== undefined ? effectiveWeight : 0;
    
    // 賞金情報を取得（prize_money.total_prize または latestAuction.total_prize_latest から取得）
    let prizeMoney = 0;
    if (horse.prize_money?.total_prize) {
      // 数値の場合はそのまま、文字列の場合は数値に変換
      if (typeof horse.prize_money.total_prize === 'number') {
        prizeMoney = horse.prize_money.total_prize;
      } else {
        // 文字列の場合は数値に変換
        const prizeStr = String(horse.prize_money.total_prize).replace(/[^0-9]/g, '');
        prizeMoney = parseInt(prizeStr, 10) || 0;
      }
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
      imageUrl = horse.image_url;
    }
    const imageUrlNormalized = normalizeImageUrl(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001', imageUrl);
    
    // 基本情報を設定
    const baseHorse: any = {
      id: horseId,
      name: horse.name || '不明',
      age: typeof horse.age === 'number' ? horse.age : (parseInt(horse.age) || 0),
      sex: horse.sex || '不明',
      sire: horse.sire || '不明',
      dam: horse.dam || '不明',
      damsire: horse.damsire || '不明',
      image_url: horse.image_url || '',
      jbis_url: horse.jbis_url || '',
      auction_url: horse.auction_url || '',
      disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags : [],
      created_at: horse.created_at || new Date().toISOString(),
      updated_at: horse.updated_at || new Date().toISOString(),
      // オークション関連情報
      auction_date: horse.auction_date || latestAuction.auction_date || '',
      sold_price: soldPrice,
      seller: horse.seller || latestAuction.seller || '不明',
      weight: horse.weight || latestAuction.weight || 0,
      total_prize_start: horse.total_prize_start || 0,
      total_prize_latest: horse.total_prize_latest || 0,
      // 主取り（unsold）の判定
      unsold: isUnsold,
      unsold_count: auctionHistory.filter((a: any) => a.sold_price === null || a.sold_price === 0).length,
      comment: horse.comment || '',
      // 計算フィールド
      roi: 0,
      price_per_kg: 0,
      display_price: '',  // 後で設定
      display_weight: '',
      display_prize: '',
      display_roi: '',
      sort_price: 0,
      sort_prize: 0,
      sort_roi: 0,
      primary_image: imageUrlNormalized,
      detail_url: horse.auction_url || `#/horse/${horseId}`,
      auction_history: auctionHistory,
      // その他の必須フィールド
      is_auction: false,
      is_new: false,
      is_updated: false,
      is_featured: false,
      is_sold: false,
      is_unsold: isUnsold,
      is_withdrawn: false,
      is_reserved: false,
      is_favorite: false,
      is_watchlist: false,
      is_compare: false,
      is_selected: false,
      is_loading: false,
      is_error: false,
      error_message: ''
    };
    
    // 賞金を適切に取得（prize_moneyオブジェクトまたはtotal_prize_latestから）
    const prizeMoneyValue = (() => {
      // 1. prize_moneyオブジェクトから取得を試みる
      if (horse.prize_money?.total_prize) {
        let prize: number;
        if (typeof horse.prize_money.total_prize === 'number') {
          prize = horse.prize_money.total_prize;
        } else {
          const prizeStr = String(horse.prize_money.total_prize).replace(/[^0-9]/g, '');
          prize = parseInt(prizeStr, 10);
        }
        if (!isNaN(prize) && prize > 0) {
          console.log(`[${index}] ${horse.name} - using prize_money.total_prize:`, prize);
          return prize;
        }
      }
      
      // 2. total_prize_latestから取得を試みる
      if (baseHorse.total_prize_latest) {
        console.log(`[${index}] ${horse.name} - using total_prize_latest:`, baseHorse.total_prize_latest);
        return baseHorse.total_prize_latest;
      }
      
      // 3. デフォルト値
      console.log(`[${index}] ${horse.name} - no prize money found, using 0`);
      return 0;
    })();
    // 計算フィールドを設定
    const soldPriceValue = typeof baseHorse.sold_price === 'number' 
      ? baseHorse.sold_price 
      : 0;
    // 重量あたりの価格を計算するための重み（0除算を防ぐため1kgをデフォルト値に）
    const weightForCalc = effectiveWeight !== undefined && effectiveWeight > 0 ? effectiveWeight : 1;
    
    // ROI計算
    const calculatedRoiValue = soldPriceValue > 0 
      ? ((prizeMoneyValue - soldPriceValue) / soldPriceValue) * 100 
      : 0;
    
    // 重量あたりの価格を計算（0除算を防ぐ）
    const pricePerKgValue = numericSoldPrice / weightForCalc;
    
    // 更新された馬データを返す
    return {
      ...baseHorse,
      roi: calculatedRoiValue,
      price_per_kg: pricePerKgValue,
      display_price: getDisplayPrice({
        unsold: isUnsold,
        sold_price: soldPrice,
        history: auctionHistory
      }),
      // 馬体重を数値のみで保持（表示時にkgを付与）
      weight: horseWeight,  // 数値のみを保持
      display_weight: horseWeight !== null ? `${horseWeight}kg` : '-',
      display_prize: getDisplayPrice({ price: prizeMoneyValue }),
      display_roi: calculatedRoiValue > 0 ? `${calculatedRoiValue.toFixed(1)}%` : '-',
      sort_price: soldPriceValue,
      sort_prize: prizeMoneyValue,
      sort_roi: calculatedRoiValue,
      primary_image: imageUrlNormalized,
      seller: latestAuction?.seller || '',
      auction_date: latestAuction?.auction_date || '',
      comment: latestAuction?.comment || '',
      effectiveAuction: effectiveAuction,
      // 外部リンクを追加（データに合わせて調整）
      jbis_url: horse.jbis_url,
      detail_url: horse.detail_url,
      // rakuten_urlが存在しない場合はdetail_urlを使用
      rakuten_url: horse.rakuten_url || horse.detail_url,
      // auction_urlが存在しない場合はdetail_urlを使用
      auction_url: horse.auction_url || horse.detail_url
    } as AnalysisHorse;
    });
    
    // Filter out any null values and ensure we have AnalysisHorse[] type
    const finalHorses = result.filter((horse: AnalysisHorse | null): horse is AnalysisHorse => horse !== null);
    
    console.log(`=== Transformation Summary ===`);
    console.log(`Total input horses: ${horsesArray.length}`);
    console.log(`Successfully transformed: ${finalHorses.length}`);
    console.log(`Failed to transform: ${horsesArray.length - finalHorses.length}`);
    
    if (finalHorses.length === 0 && horsesArray.length > 0) {
console.error('No horses were transformed successfully. First horse data:', JSON.stringify(horsesArray[0], null, 2));
      
      // デバッグ用に最初の馬のデータを簡易変換して返す
      const debugHorse = {
        ...horsesArray[0],
        id: String(horsesArray[0].id || 'debug-id'),
        name: horsesArray[0].name || 'Unknown',
        sex: horsesArray[0].sex || '不明',
        age: horsesArray[0].age || 0,
        sire: horsesArray[0].sire || '不明',
        dam: horsesArray[0].dam || '不明',
        damsire: horsesArray[0].damsire || '不明',
        effectiveAuction: {
          id: 'debug-' + (horsesArray[0].id || '1'),
          horse_id: String(horsesArray[0].id || '1'),
          auction_date: horsesArray[0].auction_date || new Date().toISOString().split('T')[0],
          sold_price: 1000, // デバッグ用の適当な値
          total_prize_start: 0,
          total_prize_latest: 0,
          weight: horsesArray[0].weight || 450, // 平均的な馬体重
          seller: horsesArray[0].seller || '不明',
          is_unsold: false,
          comment: 'デバッグ用データ',
          created_at: new Date().toISOString(),
          detail_url: horsesArray[0].detail_url || '',
          auction_url: horsesArray[0].auction_url || ''
        }
      };
      
      console.log('Debug horse data to return:', debugHorse);
      return [debugHorse as AnalysisHorse];
    }
    
    return finalHorses;
  } catch (error) {
    console.error('Error in transformHorseData:', error);
    return [];
  }
};

// formatPrice, formatWeight, formatPrizeFromYen are imported from utils/price

const calcROI = (prize: number | string | { total_prize: string } | undefined, price: number | string | undefined): string => {
  if (!prize || !price) return '-';
  
  // 賞金を数値に変換
  let prizeNum: number;
  if (typeof prize === 'object' && prize !== null && 'total_prize' in prize) {
    prizeNum = parseFloat(prize.total_prize.replace(/[^0-9.]/g, '')) || 0;
  } else if (typeof prize === 'string') {
    prizeNum = parseFloat(prize) || 0;
  } else {
    prizeNum = prize || 0;
  }
  
  // 価格を数値に変換
  const numPrice = typeof price === 'string' ? parseFloat(price) : (price || 0);
  
  if (isNaN(prizeNum) || isNaN(numPrice) || numPrice === 0) return '-';
  
  // ROIを計算（賞金 / 価格）
  const roi = (prizeNum / numPrice) * 100; // パーセント表示
  return roi.toFixed(1) + '%';
};

// 数値の平均を計算する関数
const calculateAverage = (numbers: number[]): number => {
  if (!numbers.length) return 0;
  const sum = numbers.reduce((a, b) => a + b, 0);
  return sum / numbers.length;
};

// 成長率の平均を計算する関数
const calculateAverageGrowthRate = (rates: number[]): number => {
  if (!rates.length) return 0;
  const validRates = rates.filter(rate => isFinite(rate) && !isNaN(rate));
  if (!validRates.length) return 0;
  const sum = validRates.reduce((a, b) => a + b, 0);
  return sum / validRates.length;
};

// ソートアイコンをレンダリングする関数
const renderSortIcon = (key: keyof AnalysisHorse, currentSortKey: keyof AnalysisHorse, currentSortOrder: 'asc' | 'desc') => {
  if (currentSortKey !== key) return <FaSort className="ml-1 opacity-30" />;
  return currentSortOrder === 'asc' ? (
    <FaSortUp className="ml-1" />
  ) : (
    <FaSortDown className="ml-1" />
  );
}

export default function AnalysisContent() {
  const router = useRouter();
  const [data, setData] = useState<AnalysisData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [sortKey, setSortKey] = useState<keyof AnalysisHorse>('sort_roi');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [showType, setShowType] = useState<ShowType>('all');
  const [filterBySex, setFilterBySex] = useState<string>('all');
  const [filterByAge, setFilterByAge] = useState<string>('all');
  const [filterBySire, setFilterBySire] = useState<string>('all');
  const [filterByDam, setFilterByDam] = useState<string>('all');

  // データ取得関数
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      // ローカルのJSONファイルからデータを読み込む
      const response = await fetch('/data/horses.json');
      if (!response.ok) {
        throw new Error('データの読み込みに失敗しました');
      }
      
      const horsesData = await response.json();
      
      console.log('Raw horses data:', horsesData);
      
      // データを変換
      const transformedHorses = transformHorseData(horsesData);
      
      // 統計情報を計算
      const soldPrices = transformedHorses
        .filter((h): h is AnalysisHorse & { sold_price: number } => 
          h.sold_price !== null && h.sold_price !== undefined && h.sold_price > 0)
        .map(h => h.sold_price);
      
      const growthRates = transformedHorses
        .filter((h): h is AnalysisHorse & { total_prize_start: number; total_prize_latest: number } => 
          h.total_prize_start !== undefined && 
          h.total_prize_latest !== undefined && 
          h.total_prize_start > 0 && 
          h.total_prize_latest > h.total_prize_start)
        .map(h => ((h.total_prize_latest - h.total_prize_start) / h.total_prize_start) * 100);
      
      // 分析データを設定
      const analysisData: AnalysisData = {
        horses: transformedHorses,
        last_updated: new Date().toISOString(),
        total_horses: transformedHorses.length,
        average_price: calculateAverage(soldPrices),
        average_growth_rate: calculateAverageGrowthRate(growthRates),
        horses_with_growth_data: growthRates.length
      };
      
      console.log('Transformed analysis data:', analysisData);
      setData(analysisData);
    } catch (error) {
      console.error('データの取得中にエラーが発生しました:', error);
      setError('データの取得中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // ソート関数の定義
  const sortFunctions = useMemo(() => ({
    sort_price: (a: AnalysisHorse, b: AnalysisHorse) => (a.sort_price || 0) - (b.sort_price || 0),
    sort_prize: (a: AnalysisHorse, b: AnalysisHorse) => (a.sort_prize || 0) - (b.sort_prize || 0),
    sort_roi: (a: AnalysisHorse, b: AnalysisHorse) => (a.sort_roi || 0) - (b.sort_roi || 0),
    sex: (a: AnalysisHorse, b: AnalysisHorse) => (a.sex || '').localeCompare(b.sex || '', 'ja'),
    age: (a: AnalysisHorse, b: AnalysisHorse) => (a.age || 0) - (b.age || 0),
    sire: (a: AnalysisHorse, b: AnalysisHorse) => (a.sire || '').localeCompare(b.sire || '', 'ja'),
    dam: (a: AnalysisHorse, b: AnalysisHorse) => (a.dam || '').localeCompare(b.dam || '', 'ja'),
    unsold: (a: AnalysisHorse, b: AnalysisHorse) => (a.unsold ? 1 : 0) - (b.unsold ? 1 : 0)
  }) as Record<string, (a: AnalysisHorse, b: AnalysisHorse) => number>, []);

  // ソート処理
  const handleSort = useCallback((key: keyof AnalysisHorse) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  }, [sortKey, sortOrder]);

  // ローディング中の表示
  if (loading) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }
  
  // エラーまたはデータがない場合の表示
  if (error || !data) {
    return <div className="min-h-screen flex items-center justify-center text-red-600">{error || 'データがありません'}</div>;
  }

  // データを変換
  console.log('元の馬データ:', data.horses);
  
  // 表示用の馬データを準備
  let tableHorses = data.horses.map(horse => {
    // ROIを計算
    const soldPrice = horse.sold_price || 0;
    const prizeMoney = horse.total_prize_latest || 0;
    const roi = soldPrice > 0 ? (prizeMoney / soldPrice) * 100 : 0;
    // オークション履歴を取得（auction_historyがなければ空配列を使用）
    const auctionHistory = Array.isArray(horse.auction_history) ? horse.auction_history : [];
    
    // 最新のオークション情報を取得（なければデフォルト値を使用）
    const latestAuction = auctionHistory[0] || {
      auction_date: '',
      sold_price: 0,
      is_unsold: true,
      seller: '',
      weight: 0,
      total_prize_start: 0,
      total_prize_latest: 0,
      detail_url: ''
    };

    // 有効な体重を計算
    const effectiveWeight = (() => {
      // 馬オブジェクトの体重を取得
      const horseWeight = Number(horse.weight) || 0;
      
      // オークション履歴の体重を取得
      const auctionWeight = latestAuction ? (Number(latestAuction.weight) || 0) : 0;
      
      // 有効な体重を返す（0より大きい値のみ有効）
      return (horseWeight > 0) 
        ? Math.floor(horseWeight)
        : (auctionWeight > 0)
          ? Math.floor(auctionWeight)
          : undefined;
    })();

    return {
      ...horse,
      ...latestAuction,
      effectiveWeight, // 有効な体重を追加
      unsold_count: auctionHistory.filter(a => a.is_unsold).length,
      detail_url: latestAuction.detail_url || latestAuction.auction_url || horse.detail_url || horse.auction_url || '',
      total_prize_start: latestAuction.total_prize_start,
      total_prize_latest: latestAuction.total_prize_latest || 0,
      sold_price: latestAuction.sold_price || 0,
      unsold: latestAuction.is_unsold || (horse.unsold_count ? horse.unsold_count > 0 : false),
      roi: (latestAuction.sold_price && latestAuction.sold_price > 0 && latestAuction.total_prize_latest) 
        ? (latestAuction.total_prize_latest / latestAuction.sold_price) * 100 
        : 0
    };
  });
  
  console.log('変換後の馬データ:', tableHorses);

  // 表示タイプによるフィルタリング
  if (showType === 'sold') {
    tableHorses = tableHorses.filter(horse => !horse.unsold);
  } else if (showType === 'unsold') {
    tableHorses = tableHorses.filter(horse => horse.unsold);
  } else if (showType === 'roi') {
    tableHorses = tableHorses.filter(horse => horse.roi > 0);
  } else if (showType === 'value') {
    const avgPrice = data.average_price;
    tableHorses = tableHorses.filter(horse => 
      !horse.unsold && 
      horse.sold_price && 
      horse.sold_price > 0 && 
      horse.sold_price < avgPrice && 
      horse.roi > 0
    );
  }

  // 性別によるフィルタリング
  if (filterBySex !== 'all') {
    tableHorses = tableHorses.filter(horse => horse.sex === filterBySex);
  }

  // 年齢によるフィルタリング
  if (filterByAge !== 'all') {
    tableHorses = tableHorses.filter(horse => String(horse.age) === filterByAge);
  }

  // 父馬によるフィルタリング
  if (filterBySire !== 'all') {
    tableHorses = tableHorses.filter(horse => horse.sire === filterBySire);
  }

  // 母馬によるフィルタリング
  if (filterByDam !== 'all') {
    tableHorses = tableHorses.filter(horse => horse.dam === filterByDam);
  }

  // ソート処理の適用
  console.log('ソート前の馬データ:', tableHorses);
  if (sortKey && sortFunctions[sortKey as keyof typeof sortFunctions]) {
    // 主取り馬のフィルタリングを調整
    let filteredHorses = [...tableHorses];
    // 主取り馬を除外する場合は以下のコメントアウトを外す
    // filteredHorses = filteredHorses.filter((h: AnalysisHorse) => !h.unsold_count || h.unsold_count === 0);
    tableHorses = filteredHorses.sort((a: AnalysisHorse, b: AnalysisHorse) => {
      const sortFn = sortFunctions[sortKey as keyof typeof sortFunctions];
      const result = sortFn(a, b);
      return sortOrder === 'asc' ? result : -result;
    });
  }
  const horsesWithLatest: AnalysisHorse[] = data.horses.map(horse => {
    // オークション履歴を取得（auction_historyがなければ空配列を使用）
    const auctionHistory = Array.isArray(horse.auction_history) ? horse.auction_history : [];
    
    // 馬体重を取得するヘルパー関数
    const getHorseWeight = (): number | null => {
      if (horse.weight !== undefined && horse.weight !== null && Number(horse.weight) > 0) {
        return Number(horse.weight);
      }
      
      // オークション履歴から最新の体重を確認
      if (auctionHistory.length > 0) {
        const validAuction = auctionHistory.find(a => 
          a.weight !== undefined && 
          a.weight !== null && 
          Number(a.weight) > 0
        );
        if (validAuction) {
          return Number(validAuction.weight);
        }
      }
      
      return null;
    };
    
    const currentHorseWeight = getHorseWeight();
    
    // 最新のオークション履歴を取得（存在しない場合はデフォルト値を持つオブジェクトを返す）
    const latestAuction = auctionHistory.length > 0 ? {
      ...auctionHistory[0],
      weight: auctionHistory[0].weight || currentHorseWeight
    } : {
      id: '',
      horse_id: horse.id,
      auction_date: '',
      sold_price: null,
      total_prize_start: 0,
      total_prize_latest: 0,
      weight: currentHorseWeight,
      seller: '',
      is_unsold: false,
      comment: '',
      created_at: new Date().toISOString(),
      detail_url: '',
      auction_url: ''
    };
    
    // 主取り判定
    const isUnsold = 
      horse.is_unsold === true || 
      horse.unsold === true ||
      (latestAuction && latestAuction.is_unsold === true) ||
      (latestAuction && latestAuction.unsold === true) ||
      (latestAuction && latestAuction.sold_price === 0) ||
      (horse.sold_price === 0);

    // 馬の基本情報と最新のオークション情報をマージ
    const horseWithDetails: AnalysisHorse = {
      ...horse,
      ...latestAuction,
      unsold_count: auctionHistory.filter(a => a.is_unsold).length,
      detail_url: latestAuction.detail_url || latestAuction.auction_url || horse.detail_url || horse.auction_url || '',
      total_prize_start: latestAuction.total_prize_start,
      total_prize_latest: latestAuction.total_prize_latest || 0,
      weight: latestAuction.weight,
      display_weight: latestAuction.weight !== null ? `${latestAuction.weight}kg` : '-',
      sold_price: latestAuction.sold_price !== null ? latestAuction.sold_price : (horse.sold_price || 0),
      unsold: isUnsold,
      is_unsold: isUnsold
    };

    return horseWithDetails;
  });

  // 平均ROIの計算
  const avgROI = tableHorses.length > 0 ? (
    tableHorses.reduce((sum: number, h: AnalysisHorse) => {
      const soldPrice = h.sold_price || 0;
      const prizeMoney = h.total_prize_latest || 0;
      const roi = soldPrice > 0 ? prizeMoney / soldPrice : 0;
      return sum + roi;
    }, 0) / tableHorses.length
  ) : 0;

  // ROIランキングの計算
  const roiRanking = tableHorses
    .filter((h: AnalysisHorse) => {
      const soldPrice = h.sold_price || 0;
      const prizeMoney = h.total_prize_latest || 0;
      return soldPrice > 0 && prizeMoney > 0;
    })
    .sort((a: AnalysisHorse, b: AnalysisHorse) => {
      const aROI = (a.total_prize_latest || 0) / (a.sold_price || 1);
      const bROI = (b.total_prize_latest || 0) / (b.sold_price || 1);
      return bROI - aROI;
    })
    .slice(0, 10);

  // 価値のある馬のフィルタリング
  const valueHorses = tableHorses.filter((h) => {
    const soldPrice = h.sold_price || 0;
    const prizeMoney = h.total_prize_latest || 0;
    const roi = soldPrice > 0 ? prizeMoney / soldPrice : 0;
    return soldPrice > 0 && roi > avgROI && soldPrice < data.average_price;
  });

  // 年齢を表示するヘルパー関数（スクレイピングデータをそのまま表示）
  const displayAge = (age: string | number | null | undefined): string => {
    if (age === null || age === undefined || age === '') return '-';
    return `${age}歳`;
  };

  const displayPrice = (price: number | string | null | undefined, horse: AnalysisHorse): string => {
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

    // それ以外の場合は数値に変換してからフォーマットして返す
    const priceNum = typeof price === 'string' ? parseFloat(price) : Number(price);
    return formatPrice(priceNum);
  };

  // ソート処理の適用
  console.log('フィルタリング後の馬データ:', tableHorses);
  if (sortKey && sortFunctions[sortKey]) {
    tableHorses = [...tableHorses].sort((a, b) => {
      const result = sortFunctions[sortKey](a, b);
      return sortOrder === 'asc' ? result : -result;
    });
    console.log('ソート後の馬データ:', tableHorses);
  }
  
  // Helper function to safely get detail URL
  const getDetailUrl = (horse: AnalysisHorse): string => {
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
          <span>平均落札価格: {formatPrice(data.average_price)}</span>
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
                    {horse.id ? (
                      <Link 
                        href={`/horses/${horse.id}`} 
                        className="hover:underline text-blue-700"
                        onClick={(e) => {
                          console.log('Navigating to horse:', horse.id, 'Name:', horse.name);
                        }}
                      >
                        {horse.name}
                      </Link>
                    ) : (
                      <span>{horse.name}</span>
                    )}
                  </td>
                  <td className="px-3 py-2">{horse.sex}</td>
                  <td className="px-3 py-2">{displayAge(horse.age)}</td>
                  <td className="px-3 py-2">{horse.sire}</td>
                  <td className="px-3 py-2 text-right">
                    {horse.effectiveWeight !== undefined ? `${horse.effectiveWeight}kg` : '-'}
                    {process.env.NODE_ENV === 'development' && false && (
                      <span className="text-xs text-red-500 ml-1">({horse.effectiveWeight}, type: {typeof horse.effectiveWeight})</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    {horse.display_price}
                  </td>
                  <td className="px-3 py-2">-</td>
                  <td className="px-3 py-2">
                    {horse.prize_money?.total_prize !== undefined ? getDisplayPrice({ price: horse.prize_money.total_prize }) : '-'}
                  </td>
                  <td className="px-3 py-2">
                    {horse.prize_money?.total_prize !== undefined ? 
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
        </div>
      </div>
    </div>
  );
}
