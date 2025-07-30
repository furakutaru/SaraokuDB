import * as React from 'react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, X } from "lucide-react";
import { Button } from "./ui/button";
import { useDataIntegrityCheck } from "@/hooks/useDataIntegrityCheck";

export function DataIntegrityAlert() {
  const { hasIssues, isLoading, error, totalHorses, horsesWithIssues, totalIssues, issues } = useDataIntegrityCheck();
  const [isOpen, setIsOpen] = React.useState(true);

  if (isLoading || error || !hasIssues || !isOpen) {
    return null;
  }

  const getFieldName = (field: string): string => {
    const fieldNames: Record<string, string> = {
      'sex': '性別',
      'age': '年齢',
      'sire': '父',
      'dam': '母',
      'damsire': '母父',
      'weight': '馬体重',
      'seller': '出品者',
      'auction_date': 'オークション日',
      'sold_price': '落札価格',
      'detail_url': 'オークション詳細URL',
      'image_url': '画像URL',
      'comment': 'コメント',
      'disease_tags': '病歴タグ',
      'total_prize_start': '獲得賞金（開始時）',
      'total_prize_latest': '獲得賞金（最新）',
    };

    // 履歴フィールドの処理
    const historyMatch = field.match(/history\[(\d+)\]\.(.*)/);
    if (historyMatch) {
      const historyIndex = parseInt(historyMatch[1]) + 1;
      const historyField = historyMatch[2];
      return `履歴${historyIndex}: ${getFieldName(historyField) || historyField}`;
    }

    return fieldNames[field] || field;
  };

  return (
    <Alert variant="destructive" className="mb-4">
      <AlertCircle className="h-4 w-4" />
      <div className="flex justify-between items-start">
        <div>
          <AlertTitle>データの整合性に問題があります</AlertTitle>
          <AlertDescription className="mt-2">
            <p>全{totalHorses}頭中、{horsesWithIssues}頭に合計{totalIssues}件のデータ不備が見つかりました。</p>
            <div className="mt-2">
              <p className="font-medium">主な問題:</p>
              <ul className="list-disc pl-5 mt-1 space-y-1">
                {issues.slice(0, 3).map((issue) => (
                  <li key={issue.id}>
                    {issue.name} (ID: {issue.id}): {issue.issues[0].field} - {issue.issues[0].issue}
                  </li>
                ))}
                {issues.length > 3 && <li>...他{issues.length - 3}件</li>}
              </ul>
            </div>
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
