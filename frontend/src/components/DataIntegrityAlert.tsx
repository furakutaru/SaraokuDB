import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, X } from 'lucide-react';
import { useDataIntegrityCheck, type DataIssue } from '@/hooks/useDataIntegrityCheck';

export function DataIntegrityAlert() {
  const { hasIssues, isLoading, error, totalHorses, horsesWithIssues, totalIssues, issues } = useDataIntegrityCheck();
  const [isOpen, setIsOpen] = React.useState(true);
  const [showDetails, setShowDetails] = React.useState(false);

  // エラーが発生した場合はエラーメッセージを表示
  if (error) {
    console.error('データ整合性チェックでエラーが発生しました:', error);
    return (
      <div className="p-4 bg-yellow-50 text-yellow-800 text-sm">
        <div className="flex items-center">
          <AlertCircle className="h-4 w-4 mr-2" />
          <span>データ整合性チェックでエラーが発生しました。詳細はコンソールを確認してください。</span>
        </div>
      </div>
    );
  }

  // ローディング中はスピナーを表示
  if (isLoading) {
    return (
      <div className="p-4 bg-blue-50 text-blue-800 text-sm flex items-center">
        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-800 mr-2"></div>
        <span>データ整合性を確認中...</span>
      </div>
    );
  }

  // エラーが発生した場合はエラーメッセージを表示
  if (error) {
    return (
      <Alert variant="destructive" className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <div className="flex justify-between items-start">
          <div>
            <AlertTitle>データの読み込み中にエラーが発生しました</AlertTitle>
            <AlertDescription className="mt-2">
              <p>{error}</p>
            </AlertDescription>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 p-0 text-destructive hover:bg-destructive/10"
            onClick={() => setIsOpen(false)}
          >
            <X className="h-4 w-4" />
            <span className="sr-only">閉じる</span>
          </Button>
        </div>
      </Alert>
    );
  }

  // 問題がない場合でもデータを表示する（デバッグ用）
  if (!hasIssues) {
    return (
      <Alert className="mb-4">
        <AlertCircle className="h-4 w-4" />
        <div className="flex justify-between items-start">
          <div>
            <AlertTitle>データの読み込みに成功しました</AlertTitle>
            <AlertDescription className="mt-2">
              <p>馬のデータ: {totalHorses}件</p>
              <p>オークション履歴: 0件</p>
              <Button
                variant="outline"
                size="sm"
                className="mt-2"
                onClick={() => setShowDetails(!showDetails)}
              >
                {showDetails ? '詳細を隠す' : '詳細を表示'}
              </Button>
              {showDetails && (
                <pre className="mt-2 p-2 bg-muted rounded text-xs overflow-auto max-h-60">
                  {JSON.stringify(issues, null, 2)}
                </pre>
              )}
            </AlertDescription>
          </div>
          <Button
            variant="ghost"
            size="icon"
            className="h-6 w-6 p-0 text-foreground hover:bg-foreground/10"
            onClick={() => setIsOpen(false)}
          >
            <X className="h-4 w-4" />
            <span className="sr-only">閉じる</span>
          </Button>
        </div>
      </Alert>
    );
  }

  return (
    <Alert variant="destructive" className="mb-4">
      <AlertCircle className="h-4 w-4" />
      <div className="flex flex-col space-y-2">
        <div className="flex justify-between items-start">
          <div>
            <AlertTitle>データに問題が見つかりました</AlertTitle>
            <AlertDescription className="mt-1">
              <p>{horsesWithIssues}頭の馬に合計{totalIssues}件の不整合が見つかりました。</p>
            </AlertDescription>
          </div>
          <div className="flex space-x-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-destructive hover:bg-destructive/10 h-8 px-2"
              onClick={() => setShowDetails(!showDetails)}
            >
              {showDetails ? '詳細を非表示' : '詳細を表示'}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 p-0 text-destructive hover:bg-destructive/10"
              onClick={() => setIsOpen(false)}
            >
              <X className="h-4 w-4" />
              <span className="sr-only">閉じる</span>
            </Button>
          </div>
        </div>
        
        {showDetails && (
          <div className="mt-2 text-sm border-t pt-2">
            {issues.slice(0, 10).map((issue: DataIssue) => (
              <div key={issue.id} className="mb-2 p-2 bg-destructive/5 rounded">
                <div className="font-medium">{issue.name} (ID: {issue.id})</div>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  {issue.issues.map((item: { field: string; issue: string; expected?: string }, idx: number) => (
                    <li key={idx} className="text-xs">
                      <span className="font-medium">{item.field}:</span> {item.issue}
                      {item.expected && ` (期待値: ${item.expected})`}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {issues.length > 10 && (
              <div className="text-center text-muted-foreground text-xs mt-2">
                他{issues.length - 10}件の不整合があります
              </div>
            )}
          </div>
        )}
      </div>
    </Alert>
  );
}
