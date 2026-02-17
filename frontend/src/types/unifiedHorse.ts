// Unified horse data structure types
export interface UnifiedHorse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  is_unsold: boolean;
  sold_price?: number | null;
  auction_date?: string;
  total_prize_latest: number;
  seller?: string;
  // APIからの追加フィールド
  image_url?: string;
  jbis_url?: string;
  detail_url?: string;
  is_broodmare?: boolean;
  comment?: string;
  weight?: number;
  raw_name?: string;
  primary_image?: string;
  auction_histories?: any[];
  race_record?: any;
  unified_race_records?: any;
  total_prize_start?: number;
  //
  basic_info?: BasicInfo;
  race_records?: {
    total_prize_money: number;
    last_race_date?: string;
    last_prize_update?: string;
    total_races: number;
    wins: number;
    record_format?: string;
    formatted_record?: string;
  };
  auction_history?: AuctionHistory[];
  latest_auction?: {
    date: string;
    price: number | null;
    weight: number | null;
    seller: string;
    is_unsold: boolean;
    comment?: string;
  };
  metadata: {
    created_at: string;
    updated_at: string;
    data_source: string;
  };
  disease_tags?: string[];
}

interface BasicInfo {
  name: string;
  sex: '牡' | '牝' | 'セ';
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  color?: string;
  birthday?: string;
  image_url?: string;
  jbis_url?: string;
  auction_url?: string;
  is_retired?: boolean;
  retirement_date?: string;
  disease_tags?: string[];
  comment?: string;
}

export interface AuctionHistory {
  date: string;
  price: number | null;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment?: string;
  auction_date?: string; // 互換性のため
  total_prize_start?: number; // 互換性のため
  total_prize_latest?: number; // 互換性のため
}

export interface UnifiedHorseResponse {
  metadata: {
    version: string;
    last_updated: string;
    scrape_status: {
      last_successful_scrape: string;
      next_scheduled_scrape: string;
    };
  };
  horses: UnifiedHorse[];
}
