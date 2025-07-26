export interface HorseHistory {
  auction_date?: string;
  name?: string;
  sex?: string;
  age?: string | number;
  seller?: string;
  race_record?: string;
  comment?: string;
  sold_price?: number | string;
  total_prize_start?: number;
  total_prize_latest?: number;
  detail_url?: string;
  unsold?: boolean;
  unsold_count?: number;
}

export interface Horse {
  id: number;
  name?: string;
  sex?: string;
  age?: number | string;
  sire?: string;
  dam?: string;
  seller?: string;
  sold_price?: number | string;
  auction_date?: string;
  jbis_url?: string;
  primary_image?: string;
  history?: HorseHistory[];
  detail_url?: string;
  unsold_count?: number;
  total_prize_start?: number;
  total_prize_latest?: number;
  unsold?: boolean;
}

export interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate?: number;
  horses_with_growth_data?: number;
  next_auction_date?: string;
}

export interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}
