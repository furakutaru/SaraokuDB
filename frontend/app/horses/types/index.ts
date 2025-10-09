// 馬の基本情報
export interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  auction_url: string;
  disease_tags: string[];
  weight: number | null;
  race_record: string;
  comment: string;
  created_at: string;
  updated_at: string;
  sold_price?: number | string | null;
  seller?: string;
  auction_date?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean | string;
  unsold?: boolean;
  auction_histories?: AuctionHistory[];
  [key: string]: any;
}

// オークション履歴
export interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | string | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean | string;
  unsold?: boolean;
  comment: string;
  created_at: string;
  [key: string]: any;
}

// オークション履歴の配列型
export type AuctionHistories = any[] | undefined;

// 馬データのレスポンス型
export interface HorseData {
  horses: any[];
  auctionHistories?: AuctionHistories;
  auction_histories?: AuctionHistories;
  metadata?: {
    last_updated?: string;
    total_horses?: number;
    total_auction_records?: number;
    [key: string]: any;
  };
  last_updated?: string;
  total_horses?: number;
  total_auction_records?: number;
}

// ソート順
export type SortOrder = 'asc' | 'desc';

// ソート可能なフィールド
export type SortableField = keyof Horse;
