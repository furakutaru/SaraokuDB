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

  // データの整合性をチェックする関数
  const checkDataIntegrity = useCallback(async (): Promise<void> => {
    try {
      setIsLoading(true);
      setError(null);
      
      console.log('馬データの取得を開始します...');
      const response = await fetch('/api/horses');
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`APIリクエストが失敗しました: ${response.status} ${response.statusText}\n${errorText}`);
      }
      
      const data = await response.json();
      
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
