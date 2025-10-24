// オークション履歴
export interface AuctionHistory {
  id: number | string;
  horse_id: number | string;
  auction_date: string | string[];
  sold_price: string | number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string | null;
  is_unsold: boolean;
  comment: string;
  created_at: string;
  updated_at: string;
}

// オークション情報
export interface Auction {
  id: number | string;
  auction_date: string | string[];
  sold_price: number | null;
  seller: string | null;
  is_unsold: boolean;
  [key: string]: any; // その他のプロパティに対応するため
}

// 馬の基本情報
export interface Horse {
  id: number | string;
  auction_id?: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  detail_url: string;
  auction_url: string;
  auctions?: Auction[]; // オークション情報を追加
  disease_tags?: string[];
  weight: number | null;
  race_record?: string;
  comment?: string;
  created_at?: string;
  updated_at?: string;
  sold_price?: string | number | null;
  seller?: string | null;
  auction_date?: string | string[] | null;
  unsold?: boolean;
  is_unsold?: boolean;
  total_prize_start?: number;
  total_prize_latest?: number;
  history?: AuctionHistory | AuctionHistory[];
  latestHistory?: {
    sex?: string;
    [key: string]: any;
  };
  auction_histories?: AuctionHistory[];
}

// オークション履歴の配列型
export type AuctionHistories = AuctionHistory[] | undefined;

// メタデータの型
export interface ApiMetadata {
  last_updated: string;
  total_horses: number;
  total_auction_records: number;
  [key: string]: any;
}

// 馬データのレスポンス型
export interface HorseData {
  horses: Horse[];
  auction_histories?: (AuctionHistory | null)[];
  metadata?: ApiMetadata;
}

// ページネーション情報
export interface Pagination {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
}

// フィルターオプション
export interface FilterOptions {
  sex?: string;
  minAge?: number;
  maxAge?: number;
  minPrice?: number;
  maxPrice?: number;
  searchQuery?: string;
}

// ソートオプション
export type SortOption = 'name' | 'price' | 'age' | 'date';
export type SortOrder = 'asc' | 'desc';

// ソート可能なフィールド
export type SortableField = keyof Horse;

// テーブルのカラム定義
export interface TableColumn {
  id: string;
  label: string;
  sortable?: boolean;
  align?: 'left' | 'right' | 'center';
  width?: string | number;
  format?: (value: any) => React.ReactNode;
}

// APIレスポンスの型
export interface ApiResponse<T> {
  data: T;
  pagination?: Pagination;
  error?: string;
}
