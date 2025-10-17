import React from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { AlertCircle, X } from 'lucide-react';
import { useDataIntegrityCheck } from '@/hooks/useDataIntegrityCheck';

export function DataIntegrityAlert() {
  const { hasIssues, isLoading, error, totalHorses, horsesWithIssues, totalIssues, issues } = useDataIntegrityCheck();
  const [isOpen, setIsOpen] = React.useState(true);
  const [showDetails, setShowDetails] = React.useState(false);

  // ローディング中は何も表示しない
  if (isLoading) {
    return null;
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

  // 問題がないか、アラートが閉じられている場合は何も表示しない
  if (!hasIssues || !isOpen) {
    return null;
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
            {issues.slice(0, 10).map((issue) => (
              <div key={issue.id} className="mb-2 p-2 bg-destructive/5 rounded">
                <div className="font-medium">{issue.name} (ID: {issue.id})</div>
                <ul className="list-disc list-inside mt-1 space-y-1">
                  {issue.issues.map((item, idx) => (
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
