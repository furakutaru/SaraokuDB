/**
 * 共有の馬関連の型定義
 */

// 統合されたレース記録型
export interface UnifiedRaceRecords {
  // 基本情報
  total_races: number;      // 総出走回数
  wins: number;             // 勝利数
  record_format?: string;    // レコード形式（オプショナル）
  formatted_record?: string; // フォーマット済み戦績（オプショナル）
  
  // 賞金関連
  total_prize_money: number;  // 総獲得賞金
  last_race_date?: string;    // 最終出走日
  last_prize_update?: string; // 最終賞金更新日
}

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
  
  // オークション関連
  auction_date?: string;
  sold_price?: number | null;
  is_unsold?: boolean;
  seller?: string;
  
  // 賞金関連
  total_prize_start?: number;
  total_prize_latest?: number;
  prize_money?: PrizeMoney;
  
  // 表示用のフォーマット済み文字列
  display_prize?: string;
  display_roi?: string;
  display_weight?: string;
  display_price?: string;
  
  // ソート用の数値
  sort_price?: number;
  sort_prize?: number;
  sort_roi?: number;
  
  // 計算済みの値
  roi?: number;
  price_per_kg?: number;
  effectiveWeight?: number | null;
  
  // レース記録関連（旧形式 - 互換性のため残す）
  race_record?: {
    total_races: number;
    wins: number;
    record_format: string;
    formatted_record: string;
  };
  race_records?: {
    total_prize_money: number;
    last_race_date?: string;
    last_prize_update?: string;
    [key: string]: any; // その他のプロパティも許容
  };
  
  // 統合されたレース記録
  unified_race_records?: UnifiedRaceRecords;
  
  // 互換性のためのフィールド
  /** @deprecated 代わりに detail_url を使用してください */
  auction_url?: string;
  /** @deprecated 代わりに is_unsold を使用してください */
  unsold?: boolean;
  /** @deprecated 代わりに sold_price を使用してください */
  price?: number | null;
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
