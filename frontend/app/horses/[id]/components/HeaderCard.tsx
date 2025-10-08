import React from 'react';
import Link from 'next/link';
import { Button } from '@mui/material';
import { useRouter } from 'next/navigation';

interface HeaderCardProps {
  jbisUrl?: string;
  auctionUrl?: string;
}

const HeaderCard: React.FC<HeaderCardProps> = ({ jbisUrl, auctionUrl }) => {
  const router = useRouter();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <button
            onClick={() => router.back()}
            className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            戻る
          </button>
          <div className="flex gap-4">
            <Button 
              component={Link} 
              href="/" 
              variant="outlined" 
              className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
            >
              解析
            </Button>
            <Button 
              component={Link} 
              href="/horses" 
              variant="outlined" 
              className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
            >
              直近の追加
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default HeaderCard;
