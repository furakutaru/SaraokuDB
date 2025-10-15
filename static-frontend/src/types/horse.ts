/**
 * 馬の基本情報を表すインターフェース
 */
export interface BasicInfo {
  /** 馬名 */
  name: string;
  /** 性別（牡・牝・セ） */
  sex: '牡' | '牝' | 'セ' | string;
  /** 年齢 */
  age: number;
  /** 父馬名 */
  sire: string;
  /** 母馬名 */
  dam: string;
  /** 母父名 */
  damsire: string;
  /** 馬の画像URL（オプショナル） */
  image_url?: string;
  /** JBISの詳細ページURL（オプショナル） */
  jbis_url?: string;
  /** サラブレッドオークションの詳細ページURL（オプショナル） */
  auction_url?: string;
  /** 疾病情報のタグ配列（オプショナル） */
  disease_tags?: string[];
  /** 引退フラグ（オプショナル） */
  is_retired?: boolean;
  /** 引退日（オプショナル） */
  retirement_date?: string;
}

/**
 * レース記録を表すインターフェース
 */
export interface RaceRecords {
  /** 総獲得賞金 */
  total_prize_money: number;
  /** 最終レース日（オプショナル） */
  last_race_date?: string;
  /** 最終賞金更新日時（オプショナル） */
  last_prize_update?: string;
}

/**
 * 馬の情報を表すインターフェース
 */
export interface Horse {
  /** 馬の一意識別子 */
  id: string;
  /** 基本情報 */
  basic_info: BasicInfo;
  /** レース記録 */
  race_records: RaceRecords;
  /** オークション履歴 */
  auction_history: AuctionHistory[];
  /** メタデータ */
  metadata?: {
    created_at: string;
    updated_at: string;
    data_source?: string;
  };
}

/**
 * オークション履歴を表すインターフェース
 */
export interface AuctionHistory {
  /** オークション日（YYYY-MM-DD形式） */
  date: string;
  /** 落札価格（未落札の場合はnull） */
  price: number | null;
  /** 馬体重（kg、計測されていない場合はnull） */
  weight: number | null;
  /** 売主名 */
  seller: string;
  /** 主取りフラグ */
  is_unsold: boolean;
  /** コメント */
  comment?: string;
}

/**
 * メタデータを表すインターフェース
 */
export interface Metadata {
  /** バージョン */
  version: string;
  /** 最終更新日時 */
  last_updated: string;
  /** 馬の総数 */
  total_horses: number;
  /** スクレイピングステータス（オプショナル） */
  scrape_status?: {
    last_successful_scrape: string;
    next_scheduled_scrape: string;
  };
}

/**
 * 馬データのルートオブジェクト
 */
export interface HorseData {
  /** メタデータ */
  metadata: Metadata;
  /** 馬のリスト */
  horses: Horse[];
}
