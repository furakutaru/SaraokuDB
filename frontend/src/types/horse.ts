export interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment: string;
  created_at: string;
}

export interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number | string;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  auction_url: string;
  disease_tags: string[];
  created_at: string;
  updated_at: string;
  auction_history: AuctionHistory[];
  // 互換性のためのオプショナルフィールド
  primary_image?: string;
  detail_url?: string;
  unsold_count?: number;
  total_prize_latest?: number;
  weight?: number | null;
  sold_price?: number | null;
  seller?: string;
  auction_date?: string;
  total_prize_start?: number;
  unsold?: boolean;
  comment?: string;
}

export interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

export interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}
