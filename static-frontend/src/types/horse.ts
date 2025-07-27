export interface HorseHistory {
  auction_date: string;
  name: string;
  sex: string;
  age: string | number;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  detail_url: string;
  primary_image?: string;
  disease_tags?: string;
  weight?: number;
  unsold?: boolean;
  unsold_count?: number;
}

export interface Horse {
  id: number;
  name: string;
  sex: string;
  color: string;
  birthday: string;
  history: HorseHistory[];
  sire: string;
  dam: string;
  dam_sire: string;
  primary_image: string;
  disease_tags: string;
  jbis_url: string;
  weight: number | null;
  unsold_count: number | null;
  total_prize_latest: number;
  created_at: string;
  updated_at: string;
  unsold?: boolean;
  seller?: string;
  sold_price?: number | null;
  auction_date?: string;
  detail_url?: string;
  total_prize_start?: number;
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
