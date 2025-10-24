import { Horse, AuctionHistory } from './index';

/**
 * APIメタデータ型
 */
export interface ApiMetadata {
  /** 最終更新日時 */
  last_updated?: string;
  /** 総レコード数 */
  total?: number;
  /** スキップ数 */
  skip?: number;
  /** リミット数 */
  limit?: number;
  /** その他のメタデータ */
  [key: string]: any;
}

/**
 * 馬データのレスポンス型
 */
export interface HorseData {
  /** 馬のリスト */
  horses: Horse[];
  /** オークション履歴のリスト */
  auction_histories?: AuctionHistory[];
  /** メタデータ */
  metadata: ApiMetadata;
  /** レガシー互換用のプロパティ */
  total?: number;
  last_updated?: string;
  [key: string]: any; // その他のプロパティを許容
}

/**
 * 単一の馬データのレスポンス型
 */
export interface HorseResponse {
  /** 馬データ */
  horse?: Horse;
  /** オークション履歴 */
  auction_histories?: AuctionHistory[];
  /** メタデータ */
  metadata?: ApiMetadata;
  [key: string]: any; // その他のプロパティを許容
}

/**
 * 馬一覧取得用のパラメータ型
 */
export interface FetchHorsesParams {
  /** 最新のオークションのみ取得するか */
  latest_auction?: boolean;
  /** 取得件数 */
  limit?: number;
  /** スキップ数 */
  skip?: number;
  /** その他のパラメータ */
  [key: string]: any;
}
