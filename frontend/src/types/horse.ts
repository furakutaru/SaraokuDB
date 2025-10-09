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
  detail_url?: string; // オークション詳細ページのURL
}

/**
 * オークション履歴のインターフェース
 * 互換性のためのエイリアスを含む
 */
export interface AuctionHistory extends BaseAuctionHistory {
  /** @deprecated 代わりに is_unsold を使用してください */
  unsold?: boolean;
  /** @deprecated 代わりに detail_url を使用してください */
  auction_url?: string;
}

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
  auction_id?: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: ImageUrl | string;
  jbis_url: string;
  detail_url: string;
}

/**
 * 馬の情報を表すインターフェース
 * データベースとAPIの両方で使用される
 */
export interface Horse extends BaseHorse {
  // オプショナルな基本情報
  disease_tags?: string[];
  created_at?: string;
  updated_at?: string;
  
  // オークション関連
  sold_price?: number | null;
  is_unsold?: boolean;
  seller?: string;
  
  // 賞金関連
  total_prize_latest?: number;
  prize_money?: PrizeMoney;
  
  // 互換性のためのフィールド
  /** @deprecated 代わりに detail_url を使用してください */
  auction_url?: string;
  /** @deprecated 代わりに is_unsold を使用してください */
  unsold?: boolean;
  /** @deprecated 代わりに sold_price を使用してください */
  price?: number;
  /** @deprecated 代わりに image_url を使用してください */
  primary_image?: string;
  /** @deprecated 代わりに detail_url を使用してください */
  rakuten_url?: string;
  
  // 未落札回数
  unsold_count?: number;
  
  // 履歴情報
  auction_history?: AuctionHistory[];
  history?: AuctionHistory[]; // 互換性のため
  weight?: number | null;
}

export interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
}

/**
 * 計算済みの馬情報を表すインターフェース
 * 表示用の計算済みプロパティを含む
 */
export interface HorseWithCalculations extends Horse {
  // 計算済みの基本情報
  total_prize_start: number;
  unsold_count: number;
  roi: number;
  price_per_kg: number;
  
  // 表示用のフォーマット済み文字列
  display_price: string;
  display_weight: string;
  display_prize: string;
  display_roi: string;
  
  // ソート用の数値
  sort_price: number;
  sort_prize: number;
  sort_roi: number;
  // 互換性のためのプロパティ
  primary_image: string;
}

/**
 * 分析データを表すインターフェース
 */
/**
 * 馬のデータを表すインターフェース
 * APIレスポンスの型として使用
 */
export interface HorseData {
  metadata: Metadata;
  horses: HorseWithCalculations[];
}
