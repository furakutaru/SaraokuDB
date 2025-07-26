export interface Horse {
  id: number;
  name: string;
  sex: string | string[];
  age: number | number[] | string | string[];
  sire?: string;
  dam?: string;
  dam_sire?: string;
  race_record?: string;
  weight?: number;
  total_prize_start?: number | number[];
  total_prize_latest?: number | number[];
  sold_price?: number | number[];
  auction_date?: string | string[];
  seller?: string | string[];
  disease_tags?: string;
  comment?: string | string[];
  primary_image?: string;
  image_url?: string;
  created_at?: string;
  updated_at?: string;
  unsold_count?: number;
  jbis_url?: string;
  history?: any[];
  unsold?: boolean;
}
