import { AxiosResponse } from 'axios';
import { Horse, Metadata } from './horse';

// ページネーションされたレスポンスの型
export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    page: number;
    per_page: number;
    total_pages: number;
  };
}

// APIレスポンスの基本型
export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
  headers: any;
  config: any;
}

// 馬一覧のレスポンス型
export type HorsesResponse = Horse[] | PaginatedResponse<Horse>;

// 馬詳細のレスポンス型
export type HorseResponse = Horse;

// 統計情報のレスポンス型
export type StatisticsResponse = Metadata;

// オークション日付一覧のレスポンス型
export type AuctionDatesResponse = string[];

// エラーレスポンスの型
export interface ErrorResponse {
  message: string;
  status?: number;
  errors?: Record<string, string[]>;
}

// APIレスポンスを型安全に処理するヘルパー関数
export function handleApiResponse<T>(response: AxiosResponse<T>): T {
  return response.data;
}

// エラーハンドリング用のヘルパー関数
export function handleApiError(error: any): ErrorResponse {
  if (error.response) {
    // サーバーからエラーレスポンスがある場合
    return {
      message: error.response.data?.message || 'サーバーエラーが発生しました',
      status: error.response.status,
      errors: error.response.data?.errors,
    };
  } else if (error.request) {
    // リクエストは送信されたが、レスポンスが受け取れなかった場合
    return {
      message: 'サーバーからの応答がありません。ネットワーク接続を確認してください。',
    };
  } else {
    // リクエストの設定中にエラーが発生した場合
    return {
      message: error.message || 'リクエストの送信中にエラーが発生しました。',
    };
  }
}
