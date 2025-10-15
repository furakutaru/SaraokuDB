import * as React from 'react';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle, X } from "lucide-react";
import { Button } from "./ui/button";

export function DataIntegrityAlert() {
  const [isOpen, setIsOpen] = React.useState(true);

  // アラートを非表示にする
  if (!isOpen) {
    return null;
  }

  return (
    <Alert variant="default" className="mb-4">
      <AlertCircle className="h-4 w-4" />
      <div className="flex justify-between items-start">
        <div>
          <AlertTitle>データの整合性チェック</AlertTitle>
          <AlertDescription className="mt-2">
            データの整合性を確認中です。問題がある場合はここに表示されます。
          </AlertDescription>
        </div>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 -mt-1 -mr-2"
          onClick={() => setIsOpen(false)}
        >
          <X className="h-4 w-4" />
          <span className="sr-only">閉じる</span>
        </Button>
      </div>
    </Alert>
  );
}
