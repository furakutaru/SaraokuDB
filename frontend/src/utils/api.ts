import axios, { AxiosInstance, AxiosResponse } from 'axios';
// 型定義を直接インポート
// 型定義を直接インポート
import { 
  Horse, 
  ApiMetadata,
  AuctionHistory,
  Pagination,
  FilterOptions,
  SortOption,
  TableColumn
} from '../types/horse';

// レスポンス型を定義
interface BaseResponse<T> {
  success: boolean;
  data: T;
  error?: string;
  metadata?: ApiMetadata;
}

interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
  metadata?: ApiMetadata;
}

interface HorsesResponse extends BaseResponse<Horse[]> {
  pagination?: Pagination;
}

interface HorseResponse extends BaseResponse<Horse> {}

// 統計情報のレスポンス型
interface StatisticsData {
  totalHorses: number;
  totalAuctions: number;
  averagePrice: number;
  last_updated: string;
  total_horses: number;
  total_auction_records: number;
  [key: string]: any;
}

interface StatisticsResponse extends BaseResponse<StatisticsData> {}

interface AuctionDatesResponse extends BaseResponse<string[]> {}

interface ErrorResponse {
  success: false;
  error: string;
  message?: string;
  status?: number;
  errors?: any;
  code?: number;
}

// 直接APIのベースURLを指定
const API_BASE_URL = 'http://localhost:8001';

// Axiosインスタンスの作成
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // クッキーを送信する場合
});

// リクエストインターセプター
apiClient.interceptors.request.use(
  (config) => {
    // リクエスト送信前の処理（必要に応じて認証トークンをセットなど）
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// レスポンスを処理するヘルパー関数
function handleApiResponse<T>(response: AxiosResponse<T>): T {
  return response.data;
}

// エラーを処理するヘルパー関数
function handleApiError(error: any): ErrorResponse {
  if (error.response) {
    // サーバーからエラーレスポンスがある場合
    return {
      success: false,
      error: error.response.data?.error || 'サーバーエラーが発生しました',
      message: error.response.data?.message,
      status: error.response.status,
      errors: error.response.data?.errors,
    };
  } else if (error.request) {
    // リクエストは送信されたが、レスポンスが受け取れなかった場合
    return {
      success: false,
      error: 'サーバーからの応答がありません',
      message: 'ネットワーク接続を確認してください。',
    };
  } else {
    // リクエストの設定中にエラーが発生した場合
    return {
      success: false,
      error: 'リクエストエラー',
      message: error.message || 'リクエストの送信中にエラーが発生しました',
    };
  }
}

// レスポンスインターセプター
apiClient.interceptors.response.use(
  (response) => {
    // レスポンスデータをそのまま返す
    return response;
  },
  (error) => {
    // エラーハンドリング
    if (error.response) {
      // サーバーからのレスポンスがある場合
      console.error('API Error:', error.response.data);
      return Promise.reject(error.response.data);
    } else if (error.request) {
      // リクエストは送信されたが、レスポンスが受け取れなかった場合
      console.error('No response received:', error.request);
      return Promise.reject({ message: 'サーバーからの応答がありません。ネットワーク接続を確認してください。' });
    } else {
      // リクエストの設定中にエラーが発生した場合
      console.error('Request error:', error.message);
      return Promise.reject({ message: 'リクエストの送信中にエラーが発生しました。' });
    }
  }
);

// APIレスポンスの型定義は../types/api.tsに移動しました

// 馬関連のAPI
const horseApi = {
  // 馬一覧を取得
  getHorses: async (params?: { 
    page?: number; 
    search?: string; 
    auctionDate?: string;
    perPage?: number;
  }): Promise<Horse[]> => {
    try {
      const response = await apiClient.get<HorsesResponse>('/horses/', { 
        params: {
          page: params?.page || 1,
          search: params?.search || '',
          auction_date: params?.auctionDate,
          per_page: params?.perPage || 20,
        },
      });
      
      const data = response.data;
      
      // レスポンスがPaginatedResponse型かどうかをチェック
      if (data && typeof data === 'object' && 'data' in data && 'pagination' in data) {
        return (data as PaginatedResponse<Horse>).data;
      }
      
      // 配列が直接返ってきた場合
      if (Array.isArray(data)) {
        return data;
      }
      
      // その他の形式の場合は空配列を返す
      return [];
    } catch (error) {
      const apiError = handleApiError(error);
      console.error('Error fetching horses:', apiError.message);
      return [];
    }
  },
  
  // 馬の詳細を取得
  async getHorseById(id: string | number): Promise<Horse | null> {
    try {
      const response = await apiClient.get<HorseResponse>(`/horses/${id}`);
      return response.data.data; 
    } catch (error) {
      const apiError = handleApiError(error);
      console.error(`Error fetching horse ${id}:`, apiError.message);
      return null;
    }
  },
  
  // 馬を新規作成
  createHorse: async (horseData: Partial<Horse>): Promise<Horse | null> => {
    try {
      const response = await apiClient.post<HorseResponse>('/horses/', horseData);
      return response.data.data; // response.data を response.data.data に修正
    } catch (error) {
      const apiError = handleApiError(error);
      console.error('Error creating horse:', apiError.message);
      return null;
    }
  },
  
  // 馬の情報を更新
  updateHorse: async (id: string | number, horseData: Partial<Horse>): Promise<Horse | null> => {
    try {
      const response = await apiClient.put<HorseResponse>(`/horses/${id}`, horseData);
      return response.data.data; // response.data を response.data.data に修正
    } catch (error) {
      const apiError = handleApiError(error);
      console.error(`Error updating horse ${id}:`, apiError.message);
      return null;
    }
  },
  
  // 馬を削除
  deleteHorse: async (id: string | number): Promise<{ success: boolean; message?: string }> => {
    try {
      await apiClient.delete(`/horses/${id}`);
      return { success: true };
    } catch (error) {
      const apiError = handleApiError(error);
      console.error(`Error deleting horse ${id}:`, apiError.message);
      return { success: false, message: apiError.message };
    }
  },
};

// 統計情報関連のAPI
const statsApi = {
  // 統計情報を取得
  async getStatistics(): Promise<StatisticsData | null> {
    try {
      const response = await apiClient.get<StatisticsResponse>('/statistics/');
      // StatisticsResponse の data プロパティをそのまま返す
      return response.data.data || null;
    } catch (error) {
      const apiError = handleApiError(error);
      console.error('Error fetching statistics:', apiError.message);
      return null;
    }
  },
  
  // オークション開催日一覧を取得
  async getAuctionDates(): Promise<string[]> {
    try {
      const response = await apiClient.get<AuctionDatesResponse>('/auction-dates/');
      return Array.isArray(response.data) ? response.data : [];
    } catch (error) {
      const apiError = handleApiError(error);
      console.error('Failed to fetch auction dates:', apiError.message);
      return [];
    }
  }
};

export { apiClient, horseApi, statsApi };

export default {
  horse: horseApi,
  stats: statsApi,
};
