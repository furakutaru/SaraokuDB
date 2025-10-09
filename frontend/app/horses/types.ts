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
}

// オークション履歴
interface AuctionHistory {
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
type SortOption = 'name' | 'price' | 'age' | 'date';
type SortOrder = 'asc' | 'desc';

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
