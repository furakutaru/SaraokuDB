/**
 * 共有の馬関連の型定義
 */

// オークション履歴の基本インターフェース
export interface BaseAuctionHistory {
  id: string | number;
  horse_id: string | number;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment: string;
  created_at: string;
  updated_at?: string;
  detail_url?: string;
  auction_url?: string; // 互換性のためのエイリアス
  price?: number; // 互換性のためのエイリアス (sold_price の別名)
  unsold?: boolean; // 互換性のためのエイリアス (is_unsold の別名)
}

/**
 * オークション履歴のインターフェース
 * BaseAuctionHistory を拡張
 */
export interface AuctionHistory extends BaseAuctionHistory {}

// 賞金情報のインターフェース
export interface PrizeMoney {
  total_prize: string;
}

// 画像URLのインターフェース
export interface ImageUrl {
  image_url: string;
}

// 馬の基本情報のインターフェース
export interface BaseHorse {
  id: string | number;
  name?: string;
  auction_id?: string;
  sex: string;
  sire: string;
  dam: string;
  damsire: string;
  image_url: ImageUrl | string;
  jbis_url?: string;
  detail_url?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * 馬の情報を表すインターフェース
 */
export interface Horse extends BaseHorse {
  // 基本情報
  birth_year?: number;
  age?: number;
  color?: string;
  breeder?: string;
  owner?: string;
  trainer?: string;
  location?: string;
  
  // オークション情報
  auction_date?: string;
  sold_price?: number | null;
  is_unsold?: boolean;
  seller?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  
  // 血統情報
  pedigree?: string;
  dam_sire?: string; // 互換性のため
  
  // 最新のオークション情報
  latestAuction?: {
    id: string | number;
    horse_id: string | number;
    auction_date: string;
    sold_price: number | null;
    total_prize_start: number;
    total_prize_latest: number;
    weight: number | null;
    seller: string;
    is_unsold: boolean;
    comment: string;
    created_at: string;
  } | null;
  
  // 表示用フィールド
  prize_money?: PrizeMoney;
  display_prize?: string;
  display_roi?: string;
  display_weight?: string;
  display_price?: string;
  
  // ソート用フィールド
  sort_price?: number;
  sort_prize?: number;
  sort_roi?: number;
  
  // 計算フィールド
  roi?: number;
  price_per_kg?: number;
  effectiveWeight?: number | null;
  
  // 疾病情報
  disease_tags?: string[];
  
  // 互換性のためのエイリアス
  auction_url?: string;
  unsold?: boolean; // is_unsold のエイリアス
  price?: number | null; // sold_price のエイリアス
  
  // その他のフィールド
  [key: string]: any;
}

// メタデータのインターフェース
export interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

/**
 * 計算済みの馬情報を表すインターフェース
 */
export interface HorseWithCalculations extends Horse {
  total_prize_start: number;
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
  
  // オークション関連のプロパティ
  auction_history?: AuctionHistory[];
  weight?: number | null;
  effectiveAuction?: AuctionHistory;
  is_unsold?: boolean;
  unsold?: boolean;
  sold_price?: number | null;
  seller?: string;
  auction_date?: string;
  comment?: string;
  
  // その他のプロパティ
  [key: string]: any; // 動的なプロパティに対応
}

/**
 * 馬のデータを表すインターフェース
 * APIレスポンスの型として使用
 */
export interface HorseData {
  metadata: Metadata;
  horses: HorseWithCalculations[];
  auction_history?: AuctionHistory[];
}
