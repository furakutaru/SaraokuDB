import { useState, useEffect, useCallback } from 'react';
import type { Horse } from '@/types/horse';

// データの問題点を表すインターフェース
export interface DataIssue {
  id: number;
  name: string;
  issues: {
    field: string;
    issue: string;
    value: any;
    expected?: string;
  }[];
}

// データ整合性チェックの結果を表すインターフェース
interface DataIntegrityCheckResult {
  hasIssues: boolean;
  totalHorses: number;
  horsesWithIssues: number;
  totalIssues: number;
  issues: DataIssue[];
  lastChecked: string;
}

// フックの戻り値の型
export interface UseDataIntegrityCheckReturn extends DataIntegrityCheckResult {
  isLoading: boolean;
  error: string | null;
  lastChecked: string;
}

// 必須フィールドの定義
const REQUIRED_FIELDS = ['id', 'name', 'sex', 'age', 'sire', 'dam'];

// APIリクエストのリトライ設定
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000; // 1秒

/**
 * データの整合性をチェックするカスタムフック
 */
export const useDataIntegrityCheck = (): UseDataIntegrityCheckReturn => {
  // 状態管理
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DataIntegrityCheckResult>({
    hasIssues: false,
    totalHorses: 0,
    horsesWithIssues: 0,
    totalIssues: 0,
    issues: [],
    lastChecked: ''
  });

  // リトライ付きでAPIリクエストを実行する関数
  const fetchWithRetry = async (url: string, retries = MAX_RETRIES): Promise<any> => {
    try {
      const fullUrl = url.startsWith('http') ? url : `http://localhost:8001${url}`;
      console.log(`リクエストを実行中: ${fullUrl} (残りリトライ回数: ${retries})`);
      
      const response = await fetch(fullUrl, {
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        cache: 'no-store'
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error(`リクエストが失敗しました (${MAX_RETRIES - retries + 1}/${MAX_RETRIES}):`, { 
          status: response.status, 
          statusText: response.statusText,
          error: errorText 
        });
        
        if (retries > 0) {
          console.log(`${RETRY_DELAY}ms後にリトライします...`);
          await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
          return fetchWithRetry(url, retries - 1);
        }
        
        throw new Error(`APIリクエストが失敗しました: ${response.status} ${response.statusText} ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`リクエスト中にエラーが発生しました (${MAX_RETRIES - retries + 1}/${MAX_RETRIES}):`, error);
      
      if (retries > 0) {
        console.log(`${RETRY_DELAY}ms後にリトライします...`);
        await new Promise(resolve => setTimeout(resolve, RETRY_DELAY));
        return fetchWithRetry(url, retries - 1);
      }
      
      throw error;
    }
  };

  // データの整合性をチェックする関数
  const checkDataIntegrity = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('馬データの取得を開始します...');
      
      // リクエストの詳細をログに出力
      const requestUrl = '/api/horses';
      console.log(`リクエストURL: ${requestUrl}`);
      
      // リトライ付きでデータを取得
      const data = await fetchWithRetry(requestUrl);
      console.log('データを正常に取得しました。検証を開始します...');
      
      // データの検証
      const issues: DataIssue[] = [];
      let horses: Horse[] = [];
      
      // データの形式を検証
      if (Array.isArray(data)) {
        horses = data;
      } else if (data && typeof data === 'object') {
        if (Array.isArray(data.horses)) {
          horses = data.horses;
        } else if (Array.isArray(data.data)) {
          horses = data.data;
        } else if (data.results && Array.isArray(data.results)) {
          horses = data.results;
        } else {
          // その他の形式の場合は値がオブジェクトの配列か確認
          const values = Object.values(data);
          if (values.every(item => item && typeof item === 'object' && 'id' in item)) {
            horses = values as Horse[];
          } else {
            throw new Error('無効なデータ形式です: 馬データの配列が見つかりません');
          }
        }
      } else {
        throw new Error('無効なデータ形式です: 配列またはオブジェクトである必要があります');
      }
      
      // 必須フィールドのチェック
      horses.forEach(horse => {
        const horseIssues: DataIssue['issues'] = [];
        
        REQUIRED_FIELDS.forEach(field => {
          if (!(field in horse) || 
              horse[field as keyof Horse] === null || 
              horse[field as keyof Horse] === undefined || 
              horse[field as keyof Horse] === '') {
            horseIssues.push({
              field,
              issue: '必須フィールドが不足しています',
              value: horse[field as keyof Horse],
              expected: '空でない値が設定されていること'
            });
          }
        });
        
        if (horseIssues.length > 0) {
          issues.push({
            id: Number(horse.id) || -1, // 明示的に数値に変換
            name: String(horse.name || '名前不明'),
            issues: horseIssues
          });
        }
      });
      
      // 結果を更新
      const newResult: DataIntegrityCheckResult = {
        hasIssues: issues.length > 0,
        totalHorses: horses.length,
        horsesWithIssues: new Set(issues.map(issue => issue.id)).size,
        totalIssues: issues.reduce((sum, issue) => sum + issue.issues.length, 0),
        issues,
        lastChecked: new Date().toISOString()
      };
      
      setResult(newResult);
      setError(null);
      
    } catch (error) {
      console.error('データ整合性チェックエラー:', error);
      const errorMessage = error instanceof Error ? error.message : '不明なエラーが発生しました';
      setError(errorMessage);
      
      // エラー時の結果を設定
      setResult({
        hasIssues: true,
        totalHorses: 0,
        horsesWithIssues: 0,
        totalIssues: 1,
        issues: [{
          id: -1,
          name: 'システムエラー',
          issues: [{
            field: 'system',
            issue: 'データの取得に失敗しました',
            value: errorMessage,
            expected: '正常なデータ取得'
          }]
        }],
        lastChecked: new Date().toISOString()
      });
    } finally {
      setIsLoading(false);
    }
  }, []);

  // コンポーネントのマウント時に実行
  useEffect(() => {
    checkDataIntegrity();
  }, [checkDataIntegrity]);

  // 戻り値
  return {
    ...result,
    isLoading,
    error,
    lastChecked: result.lastChecked
  };
};
