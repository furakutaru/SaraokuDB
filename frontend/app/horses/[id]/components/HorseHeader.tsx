import React from 'react';
import { Button } from '@mui/material';
import Link from 'next/link';

interface HorseHeaderProps {
  // シンプルなヘッダーなので、必要なプロパティのみを保持
  title?: string;
}

/**
 * 馬の詳細ページ用のシンプルなヘッダーコンポーネント
 */
export const HorseHeader: React.FC<HorseHeaderProps> = ({
  title = '馬の詳細'
}) => {
  return (
    <header className="bg-white shadow-sm border-b p-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
        
        <div className="flex items-center gap-2">
          <Link
            href="/"
            className="rounded-md bg-white border border-black text-black px-3 py-1.5 text-sm hover:bg-gray-100 transition-colors flex items-center"
          >
            解析
          </Link>
          <Link
            href="/horses"
            className="rounded-md bg-white border border-black text-black px-3 py-1.5 text-sm hover:bg-gray-100 transition-colors flex items-center"
          >
            直近の追加
          </Link>
          <Button 
            variant="outlined"
            size="small"
            onClick={() => window.history.back()}
            className="self-center"
            startIcon={
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
            }
          >
            戻る
          </Button>
        </div>
      </div>
    </header>
  );
};

export default HorseHeader;
