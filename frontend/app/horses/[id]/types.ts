import { BaseAuctionHistory } from '../../../src/types/horse';

// レース成績の型定義
export type RaceRecord = string | {
  total_races?: number;
  wins?: number;
  seconds?: number;
  thirds?: number;
  record_format?: string;
  formatted_record?: string;
  unified_race_records?: boolean;
  [key: string]: any;
};

// BaseAuctionHistoryから必要なプロパティを継承
interface ExtendedBaseAuctionHistory {
  id: string | number;
  horse_id: string | number;
  auction_date: string | string[];
  price: number | null;  // データベースの price カラムにマッピング
  sold_price?: number | null; // 後方互換性のため残す（非推奨）
  total_prize_start: number;
  total_prize_latest: number | null;
  weight: number | null;
  seller: string | null;
  is_unsold: boolean;
  unsold: boolean;
  comment: string | null;
  created_at: string;
  updated_at: string;
  detail_url: string | null;
  auction_url: string | null;
  name: string | null;
  sex: string | null;
  age: string | number | null;
  race_record: RaceRecord | null;
  primary_image: string | null;
  disease_tags: string | null;
  [key: string]: any; // 他のプロパティを許容
}

// オークション履歴の拡張型
export interface ExtendedAuctionHistory extends Omit<ExtendedBaseAuctionHistory, 'race_record'> {
  race_record?: RaceRecord | string | null;
}
