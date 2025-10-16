/**
 * 馬の基本情報
 */
export interface Horse {
  /** 馬ID (UUID) */
  id: string;
  /** 馬名 */
  name: string;
  /** 性別 */
  sex: string;
  /** 年齢 */
  age: number;
  /** 父馬名 */
  sire: string;
  /** 母馬名 */
  dam: string;
  /** 母父名 */
  damsire: string;
  /** 画像URL */
  image_url: string;
  /** JBISのURL */
  jbis_url: string;
  /** オークションURL */
  auction_url: string;
  /** 疾病タグ */
  disease_tags: string[];
  /** 馬体重 (kg) */
  weight: number | null;
  /** レース戦績 */
  race_record: string;
  /** コメント */
  comment: string;
  /** 作成日時 */
  created_at: string;
  /** 更新日時 */
  updated_at: string;
  /** 落札価格 */
  sold_price?: number | string | null;
  /** 販売者 */
  seller?: string;
  /** オークション日 */
  auction_date?: string;
  /** オークション時点の総賞金 */
  total_prize_start?: number;
  /** 最新の総賞金 */
  total_prize_latest?: number;
  /** 主取りフラグ (レガシー互換用) */
  is_unsold?: boolean | string;
  /** 主取りフラグ */
  unsold?: boolean;
  /** オークション履歴 */
  auction_histories?: AuctionHistory[];
  /** その他のプロパティ */
  [key: string]: any;
}

/**
 * オークション履歴
 */
export interface AuctionHistory {
  /** 履歴ID (UUID) */
  id: string;
  /** 馬ID */
  horse_id: string;
  /** オークション日 */
  auction_date: string;
  /** 落札価格 */
  sold_price: number | string | null;
  /** オークション時点の総賞金 */
  total_prize_start: number;
  /** 最新の総賞金 */
  total_prize_latest: number;
  /** 馬体重 (kg) */
  weight: number | null;
  /** 販売者 */
  seller: string;
  /** 主取りフラグ (レガシー互換用) */
  is_unsold: boolean | string;
  /** 主取りフラグ */
  unsold?: boolean;
  /** コメント */
  comment: string;
  /** 作成日時 */
  created_at: string;
  /** その他のプロパティ */
  [key: string]: any;
}

/**
 */
export type AuctionHistories = AuctionHistory[] | undefined;

/**
 * 馬データのレスポンス型
 */
export interface HorseData {
  /** 馬の配列 */
  horses: Horse[];
  /** オークション履歴 (キャメルケース版) */
  auctionHistories?: AuctionHistory[];
  /** オークション履歴 (スネークケース版) */
  auction_histories?: AuctionHistory[];
  /** メタデータ */
  metadata?: {
    /** 最終更新日時 */
    last_updated?: string;
    /** 総馬数 */
    total_horses?: number;
    /** 総オークション記録数 */
    total_auction_records?: number;
    /** その他のメタデータ */
    [key: string]: any;
  };
  /** その他のプロパティ */
  [key: string]: any;
}

/**
 * ソート順
 */
export type SortOrder = 'asc' | 'desc';

/**
 * ソート可能なフィールド
 */
export type SortableField = 'name' | 'age' | 'sold_price' | 'auction_date' | 'total_prize_latest';

// コンポーネントの型定義を再エクスポート
export * from './components/Button.types';
export * from './components/HorseImage.types';

// API関連の型定義を再エクスポート
export * from './api/horses.types';
