'use client';

import React from 'react';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <h1 className="text-xl font-semibold">サラオクDB</h1>
            <div className="flex gap-4">
              <Link href="/" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors">解析</Link>
              <Link href="/horses" className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100">直近の追加</Link>
            </div>
          </div>
        </div>
      </header>

      {/* メイン */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow p-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">サラオクDBへようこそ</h2>
          <p className="text-gray-600 mb-8">競走馬のオークション情報を管理するプラットフォーム</p>
          <div className="flex flex-wrap gap-3">
            <Link 
              href="/horses" 
              className="rounded-md bg-blue-600 text-white px-6 py-3 hover:bg-blue-700 transition-colors"
            >
              馬の一覧を見る
            </Link>
            <Link 
              href="/" 
              className="rounded-md bg-white border border-black text-black px-6 py-3 hover:bg-gray-100 transition-colors"
            >
              解析トップへ
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
