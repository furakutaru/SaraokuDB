// 必要な型を直接インポート
import type { Horse } from '../types/horse';
import type { ApiMetadata } from '../types/horse';
import type { Pagination } from '../types/horse';

/**
 * 基本的なAPIレスポンスの型
 */
interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

/**
 * ページネーションされたレスポンスの型
 */
interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
  metadata?: ApiMetadata;
}

/**
 * 馬一覧のレスポンス型
 */
interface HorsesResponse extends ApiResponse<Horse[]> {
  pagination?: Pagination;
}

/**
 * 馬1件のレスポンス型
 */
interface HorseResponse extends ApiResponse<Horse> {}

/**
 * 統計情報のレスポンス型
 */
interface StatisticsResponse extends ApiResponse<{
  totalHorses: number;
  totalAuctions: number;
  averagePrice: number;
  metadata: ApiMetadata;
}> {}

/**
 * オークション開催日のレスポンス型
 */
interface AuctionDatesResponse extends ApiResponse<string[]> {}

/**
 * エラーレスポンスの型
 */
interface ErrorResponse {
  success: false;
  error: string;
  message?: string;
  status?: number;
  errors?: any;
  code?: number;
}

export type {
  ApiResponse,
  PaginatedResponse,
  HorsesResponse,
  HorseResponse,
  StatisticsResponse,
  AuctionDatesResponse,
  ErrorResponse
};
