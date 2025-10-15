// 馬の基本情報
export interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  image_url: string;
  jbis_url: string;
  auction_url: string;
  disease_tags: string[];
  weight: number | null;
  race_record: string;
  comment: string;
  created_at: string;
  updated_at: string;
  sold_price?: number | null;
  seller?: string;
  auction_date?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  is_unsold?: boolean;
  auction_histories?: AuctionHistory[];
  latestHistory?: {
    sex?: string;
    [key: string]: any;
  };
}

// オークション履歴
export interface AuctionHistory {
  id: string;
  horse_id: string;
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  total_prize_latest: number;
  weight: number | null;
  seller: string;
  is_unsold: boolean;
  comment: string;
  created_at: string;
}

// オークション履歴の配列型
export type AuctionHistories = AuctionHistory[] | undefined;

// 馬データのレスポンス型
export interface HorseData {
  horses: Horse[];
  auctionHistories?: AuctionHistory[];
  auction_histories?: AuctionHistory[];
  metadata?: {
    last_updated?: string;
    total_horses?: number;
    total_auction_records?: number;
    [key: string]: any;
  };
  last_updated?: string;
  total_horses?: number;
  total_auction_records?: number;
}

// ページネーション情報
interface Pagination {
  currentPage: number;
  totalPages: number;
  totalItems: number;
  itemsPerPage: number;
}

// フィルターオプション
interface FilterOptions {
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
