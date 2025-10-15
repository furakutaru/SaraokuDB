import { BaseAuctionHistory } from '@/src/types/horse';

// レース成績の型定義
export type RaceRecord = string | {
  total_races?: number;
  wins?: number;
  seconds?: number;
  thirds?: number;
  record_format?: string;
  formatted_record?: string;
  [key: string]: any;
};

// オークション履歴の拡張型
export interface ExtendedAuctionHistory extends Omit<BaseAuctionHistory, 'race_record'> {
  name?: string;
  sex?: string;
  age?: string | number;
  race_record?: RaceRecord | string;
  primary_image?: string;
  disease_tags?: string;
  detail_url?: string;
  unsold?: boolean;
}
