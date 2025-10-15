import React from 'react';
import Link from 'next/link';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  showBackButton?: boolean;
  onBackClick?: () => void;
}

const PageHeader: React.FC<PageHeaderProps> = ({ 
  title, 
  subtitle = '次回更新: 毎週木・日 24:00',
  showBackButton = false,
  onBackClick
}) => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center">
            {showBackButton ? (
              <button
                onClick={onBackClick}
                className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors flex items-center mr-4"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                戻る
              </button>
            ) : (
              <div>
                <h1 className="text-xl font-semibold text-gray-900">{title}</h1>
                {subtitle && <p className="text-sm text-gray-500">{subtitle}</p>}
              </div>
            )}
          </div>
          <div className="flex gap-4">
            {/* ボタンはHorseHeaderに移動しました */}
          </div>
        </div>
      </div>
    </header>
  );
};

export default PageHeader;
