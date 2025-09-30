export interface AuctionHistory {
  id: string | number;
  horse_id: string | number;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  unsold?: boolean; // 互換性のためのエイリアス
  comment: string;
  created_at: string;
  detail_url?: string; // オークション詳細ページのURL
  auction_url?: string; // 互換性のためのエイリアス
}

export interface PrizeMoney {
  total_prize: string;
}

export interface ImageUrl {
  image_url: string;
}

export interface Horse {
  id: string | number;  // データベースのID（数値）
  auction_id?: string;  // オークションサイトのID（文字列）
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: ImageUrl | string;
  jbis_url: string;
  auction_url?: string;
  disease_tags?: string[];
  created_at?: string;
  updated_at?: string;
  total_prize_latest?: number;
  comment?: string;
  detail_url: string;
  prize_money?: PrizeMoney;
  is_unsold?: boolean;
  sold_price: number | null;
  unsold?: boolean;
  seller?: string;  // 販売者情報を追加
  // 互換性のためのフィールド
  auction_history?: AuctionHistory[];
  weight?: number | null;
}

export interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

export interface HorseWithCalculations extends Horse {
  history?: AuctionHistory[];
  auction_history?: AuctionHistory[];
  total_prize_start: number;
  total_prize_latest: number;
  unsold_count: number;
  roi: number;
  price_per_kg: number;
  display_price: string;
  display_weight: string;
  display_prize: string;
  display_roi: string;
  sort_price: number;
  sort_prize: number;
  sort_roi: number;
  primary_image: string;
  seller: string;
  auction_date: string;
  comment: string;
  unsold: boolean;
}

export interface AnalysisData {
  horses: HorseWithCalculations[];
  metadata: {
    last_updated: string;
    total_horses: number;
    average_price: number;
    average_growth_rate: number;
    horses_with_growth_data: number;
  };
}

export interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}
