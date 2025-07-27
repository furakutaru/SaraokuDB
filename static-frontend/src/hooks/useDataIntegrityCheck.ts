import { useState, useEffect } from 'react';

interface DataIssue {
  id: string;
  name: string;
  issues: Array<{
    field: string;
    issue: string;
    value?: any;
  }>;
}

interface DataIntegrityResult {
  hasIssues: boolean;
  totalHorses: number;
  horsesWithIssues: number;
  totalIssues: number;
  issues: DataIssue[];
  isLoading: boolean;
  error: string | null;
}

export function useDataIntegrityCheck(): DataIntegrityResult {
  const [result, setResult] = useState<Omit<DataIntegrityResult, 'isLoading' | 'error'>>({
    hasIssues: false,
    totalHorses: 0,
    horsesWithIssues: 0,
    totalIssues: 0,
    issues: [],
  });
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const checkDataIntegrity = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // データを取得
        const response = await fetch('/data/horses_history.json');
        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }
        
        const data = await response.json();
        
        // 整合性チェックを実行
        const checkResult = await fetch('/api/check-data-integrity', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(data),
        });
        
        if (!checkResult.ok) {
          throw new Error('データの整合性チェックに失敗しました');
        }
        
        const result = await checkResult.json();
        
        setResult({
          hasIssues: result.summary.total_issues > 0,
          totalHorses: result.summary.total_horses,
          horsesWithIssues: result.summary.horses_with_issues,
          totalIssues: result.summary.total_issues,
          issues: result.issues,
        });
      } catch (err) {
        console.error('データ整合性チェックエラー:', err);
        setError('データの整合性チェック中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    checkDataIntegrity();
  }, []);

  return {
    ...result,
    isLoading,
    error,
  };
}
