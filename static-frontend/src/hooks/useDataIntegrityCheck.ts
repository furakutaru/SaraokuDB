import { useState, useEffect } from 'react';
import { HorseData, AuctionData } from '../types/horse';

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

interface DataIntegrityResult {
  hasIssues: boolean;
  totalHorses: number;
  horsesWithIssues: number;
  totalIssues: number;
  issues: DataIssue[];
  lastChecked?: string;
}

export const useDataIntegrityCheck = () => {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DataIntegrityResult>({
    hasIssues: false,
    totalHorses: 0,
    horsesWithIssues: 0,
    totalIssues: 0,
    issues: [],
  });
  const [lastChecked, setLastChecked] = useState<string>('');

  useEffect(() => {
    const checkDataIntegrity = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // データを取得
        const response = await fetch('/data/horses.json');
        
        if (!response.ok) {
          throw new Error('馬データの取得に失敗しました');
        }
        
        const data = await response.json();
        
        if (!data || typeof data !== 'object' || !Array.isArray(data.horses)) {
          throw new Error('無効なデータ形式です: horses配列が見つかりません');
        }
        
        const horsesData = data.horses;
        
        // 整合性チェックを実行
        const issues: DataIssue[] = [];
        
        // 必須フィールドのチェック
        const requiredFields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire'];
        
        horsesData.forEach((horse: any) => {
          const horseIssues: DataIssue['issues'] = [];
          
          // 必須フィールドのチェック（historyはオプショナル）
          requiredFields.forEach(field => {
            if (!(field in horse) || horse[field] === '' || horse[field] === null || horse[field] === undefined) {
              horseIssues.push({
                field,
                issue: '必須フィールドが不足しています',
                value: horse[field],
                expected: '有効な値が設定されていること'
              });
            }
          });
          
          // オークション履歴はオプショナルなため、存在チェックは行わない
          // 履歴が存在する場合のみ、その整合性をチェック
          if (horse.history && Array.isArray(horse.history) && horse.history.length > 0) {
            horse.history.forEach((auction: any, index: number) => {
              if (!auction.auction_date) {
                horseIssues.push({
                  field: `history[${index}].auction_date`,
                  issue: 'オークション日付が設定されていません',
                  value: auction.auction_date,
                  expected: '有効な日付が設定されていること'
                });
              }
              
              if (auction.sold_price === undefined || auction.sold_price === null) {
                horseIssues.push({
                  field: `history[${index}].sold_price`,
                  issue: '落札価格が設定されていません',
                  value: auction.sold_price,
                  expected: '0以上の数値が設定されていること'
                });
              }
            });
          }
          
          if (horseIssues.length > 0) {
            issues.push({
              id: horse.id,
              name: horse.name || '名前不明',
              issues: horseIssues
            });
          }
        });
        
        // 結果をセット
        const totalHorses = horsesData.length;
        const horsesWithIssues = new Set(issues.map(issue => issue.id)).size;
        const totalIssues = issues.reduce((sum, issue) => sum + issue.issues.length, 0);
        
        setResult({
          hasIssues: totalIssues > 0,
          totalHorses,
          horsesWithIssues,
          totalIssues,
          issues,
        });
        
        setLastChecked(new Date().toISOString());
      } catch (err) {
        console.error('データ整合性チェックエラー:', err);
        setError(`データの整合性チェック中にエラーが発生しました: ${err instanceof Error ? err.message : String(err)}`);
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
    lastChecked,
  };
};
