/**
 * 馬の基本情報を表すインターフェース
 */
export interface Horse {
  /** 馬の一意識別子（UUID） */
  id: string;
  /** 馬名 */
  name: string;
  /** 性別（牡・牝・セ） */
  sex: '牡' | '牝' | 'セ' | string;
  /** 年齢 */
  age: number;
  /** 毛色 */
  color?: string;
  /** 生年月日（YYYY-MM-DD形式） */
  birthday?: string;
  /** 父馬名 */
  sire: string;
  /** 母馬名 */
  dam: string;
  /** 母父名 */
  damsire: string;
  /** 馬の画像URL */
  image_url: string;
  /** JBISの詳細ページURL */
  jbis_url: string;
  /** サラブレッドオークションの詳細ページURL */
  auction_url: string;
  /** 疾病情報のタグ配列 */
  disease_tags: string[];
  /** 初回登録日時（ISO 8601形式） */
  created_at: string;
  /** 最終更新日時（ISO 8601形式） */
  updated_at: string;
  /** オークション履歴 */
  history?: AuctionHistory[];
  /** 最新のオークション情報 */
  latest_auction?: AuctionHistory;
  /** 落札価格（オプショナル） */
  sold_price?: number | null;
  /** オークション日付 */
  auction_date?: string;
  /** 売主 */
  seller?: string;
  /** コメント */
  comment?: string;
  /** 主取りフラグ */
  is_unsold?: boolean;
  /** オークション開始時の総賞金（万円） */
  total_prize_start?: number;
  /** 最新の総賞金（万円） */
  total_prize_latest?: number;
  /** 馬体重（kg、オプショナル） */
  weight?: number | null;
}

/**
 * オークション履歴を表すインターフェース
 */
export interface AuctionHistory {
  /** オークション履歴の一意識別子（UUID） */
  id: string;
  /** 馬ID（horses.idへの外部キー） */
  horse_id: string;
  /** オークション日（YYYY-MM-DD形式） */
  auction_date: string;
  /** 落札価格（未落札の場合はnull） */
  sold_price: number | null;
  /** 年齢（オプショナル） */
  age?: number;
  /** オークション時点の総賞金（万円） */
  total_prize_start: number;
  /** 最新の総賞金（万円） */
  total_prize_latest: number;
  /** 馬体重（kg、計測されていない場合はnull） */
  weight: number | null;
  /** 売り主名 */
  seller: string;
  /** 主取りフラグ */
  is_unsold: boolean;
  /** コメント */
  comment: string;
  /** 登録日時（ISO 8601形式） */
  created_at: string;
}

/**
 * メタデータを表すインターフェース
 */
export interface Metadata {
  /** 最終更新日時（ISO 8601形式） */
  last_updated: string;
  /** 馬の総数 */
  total_horses: number;
  /** データの説明 */
  description?: string;
  /** データのバージョン */
  version?: string;
  /** データソース */
  data_source?: string;
  /** 生成日時（ISO 8601形式） */
  generated_at?: string;
}

/**
 * 馬データのルートオブジェクト
 */
export interface AuctionData {
  /** メタデータ */
  metadata: Metadata;
  /** オークション履歴の配列 */
  auction_history: AuctionHistory[];
}

export interface HorseData {
  metadata: Metadata;
  horses: Horse[];
  auction_history?: AuctionHistory[];
}
