/**
 * 共有の馬関連の型定義
 * 更新日: 2025/10/30
 */

// ==================== 基本型 ====================

export type Sex = '牡' | '牝' | 'セ' | 'その他' | string;
export type Age = number | string;
export type Price = number | string | null;
export type Weight = number | string | null;

// ==================== オークション関連 ====================

/** オークション履歴の基本インターフェース */
export interface BaseAuctionHistory {
  id: string | number;
  horse_id: string | number;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: Weight;
  seller: string;
  is_unsold: boolean;
  comment: string;
  created_at: string;
  updated_at?: string;
  detail_url?: string;
  
  // 互換性のためのエイリアス
  auction_url?: string;  // 代わりに detail_url を使用
  price?: number;        // 代わりに sold_price を使用
  unsold?: boolean;      // 代わりに is_unsold を使用
}

/** オークション履歴のインターフェース */
export interface AuctionHistory extends BaseAuctionHistory {}

// ==================== 馬の基本情報 ====================

/** 賞金情報 */
export interface PrizeMoney {
  total_prize: string;
}

/** 画像URL */
export interface ImageUrl {
  image_url: string;
}

/** 馬の基本情報のインターフェース */
export interface BaseHorse {
  id: string | number;
  name: string;
  auction_id?: string;
  sex: Sex;
  sire: string;
  dam: string;
  dam_sire: string;
  image_url: ImageUrl | string;
  jbis_url?: string;
  detail_url?: string;
  created_at?: string;
  updated_at?: string;
}

// ==================== レース関連 ====================

/** レース記録 */
export interface RaceRecord {
  date: string;
  race_name: string;
  disease_tags?: string[] | null;
  total_races?: number;
  wins?: number;
  record_format?: string;
  formatted_record?: string;
  total_prize_money?: number;
  last_race_date?: string;
  last_prize_update?: string;
  [key: string]: any; // その他の動的プロパティ
}

// ==================== 馬の詳細情報 ====================

/** 馬の情報を表すインターフェース */
export interface Horse extends BaseHorse {
  // 基本情報
  birth_year?: number;
  age?: Age;
  color?: string;
  breeder?: string;
  owner?: string;
  trainer?: string;
  location?: string;
  
  // オークション関連
  auction_date?: string;
  sold_price?: Price;
  is_unsold?: boolean;
  seller?: string;
  is_broodmare?: boolean;
  raw_name?: string;
  
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
  effectiveWeight?: Weight;
  weight?: Weight;
  
  // オークション履歴
  auction_histories?: AuctionHistory[];
  
  // 病歴タグ
  disease_tags?: string[] | null;
  
  // 互換性のためのフィールド (非推奨)
  /** @deprecated 代わりに detail_url を使用してください */
  auction_url?: string;
  /** @deprecated 代わりに is_unsold を使用してください */
  unsold?: boolean;
  /** @deprecated 代わりに sold_price を使用してください */
  price?: number | null;
}

// ==================== 計算済み情報 ====================

/** 計算済みの馬情報を表すインターフェース */
export interface HorseWithCalculations extends Horse {
  // 計算済みの値
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
  
  // 画像関連
  primary_image: string;
  
  // オークション履歴
  auction_history?: AuctionHistory[];
  
  // レース関連
  race_record?: RaceRecord;
  race_records?: RaceRecord[];
  
  // 互換性のためのフィールド
  weight?: Weight;
  effectiveAuction?: AuctionHistory;
  latestAuction?: AuctionHistory;
  is_unsold?: boolean;
  unsold?: boolean;
  sold_price?: number | null;
  seller?: string;
  auction_date?: string;
  comment?: string;
  detail_url?: string;
  auction_url?: string;
  jbis_url?: string;
  
  // 病歴タグ
  disease_tags?: string[] | null;
  unified_race_records?: boolean;
}

// ==================== APIレスポンス ====================

/** 馬データのAPIレスポンス */
export interface HorseData {
  metadata: Metadata;
  horses: HorseWithCalculations[];
  auction_history?: AuctionHistory[];
}

// ==================== APIメタデータ ====================

/** APIメタデータ */
export interface ApiMetadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
  // 互換性のためのフィールド
  total?: number;
  count?: number;
  total_auctions?: number;
}

/** ページネーション情報 */
export interface Pagination {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

/** フィルターオプション */
export interface FilterOptions {
  search?: string;
  auctionDate?: string;
  page?: number;
  perPage?: number;
}

/** テーブルカラム設定 */
export interface TableColumn {
  key: keyof HorseWithCalculations;
  label: string;
  sortable?: boolean;
  width?: string;
}

// ==================== メタデータ ====================

/** APIメタデータ */
export interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
  // 互換性のためのフィールド
  total?: number;
  count?: number;
  total_auctions?: number;
}

// ==================== ページネーション ====================

/** ページネーション情報 */
export interface PaginationInfo {
  page: number;
  limit: number;
  total: number;
  totalPages: number;
}

/** ページネーション付きレスポンス */
export interface PaginatedResponse<T> {
  data: T[];
  pagination: PaginationInfo;
}

// ==================== フィルター関連 ====================

/** ソート方向 */
export type SortDirection = 'asc' | 'desc';

/** ソートオプション */
export interface SortOption {
  field: keyof HorseWithCalculations;
  direction: SortDirection;
}

/** 馬のフィルターオプション */
export interface HorseFilterOptions {
  // 基本フィルター
  name?: string;
  sex?: Sex | '';
  
  // 数値範囲フィルター
  minAge?: number;
  maxAge?: number;
  minPrice?: number;
  maxPrice?: number;
  minWeight?: number;
  maxWeight?: number;
  
  // オークションフィルター
  seller?: string;
  is_unsold?: boolean;
  
  // ソート
  sortBy?: keyof HorseWithCalculations;
  sortOrder?: SortDirection;
  
  // ページネーション
  page?: number;
  limit?: number;
}

// ==================== フォーム関連 ====================

/** 馬情報フォームの値 */
export interface HorseFormValues {
  name: string;
  sex: Sex | '';
  age: string;
  weight: string;
  price: string;
  seller: string;
  comment: string;
}

// ==================== ユーティリティ型 ====================

/** 必須フィールドを指定する型 */
export type RequiredField<T, K extends keyof T> = T & {
  [P in K]-?: T[P];
};

/** 部分的に更新可能な型 */
export type PartialHorse = Partial<Horse>;
