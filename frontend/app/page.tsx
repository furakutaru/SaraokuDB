'use client';

import React from 'react';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-gray-50">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-800 mb-6">サラオクDBへようこそ</h1>
        <p className="text-gray-600 mb-8">競走馬のオークション情報を管理するプラットフォーム</p>
        <div className="space-y-4">
          <Link 
            href="/horses" 
            className="inline-block px-8 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
          >
            馬の一覧を見る
          </Link>
        </div>
      </div>
    </div>
  );
}
