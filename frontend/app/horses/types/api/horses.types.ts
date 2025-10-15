import { Horse, AuctionHistory } from '..';

/**
 * 馬一覧取得APIのレスポンス型
 */
export interface HorsesListResponse {
  success: boolean;
  data: {
    horses: Horse[];
    total: number;
  };
  error?: string;
}

/**
 * オークション履歴取得APIのレスポンス型
 */
export interface AuctionHistoriesResponse {
  success: boolean;
  data: {
    histories: AuctionHistory[];
    total: number;
  };
  error?: string;
}

/**
 * エラーレスポンス型
 */
export interface ApiErrorResponse {
  success: false;
  error: string;
}
