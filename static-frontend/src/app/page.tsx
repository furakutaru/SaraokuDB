'use client';

import { Button } from '@/components/ui/button';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import AnalysisContent from '@/components/AnalysisContent';

export default function Home() {
  const router = useRouter();
  
  // ヘッダー部分を残して、コンテンツ部分をAnalysisContentに置き換え
  return (
    <>
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-4">
              <h1 className="text-2xl font-bold text-gray-900">サラオクDB</h1>
              <div className="hidden md:flex items-center text-sm text-gray-600 border-l border-gray-300 pl-4">
                <span>次回更新: </span>
                <span className="font-medium ml-1">毎週木・日 24:00</span>
              </div>
            </div>
            <div className="flex gap-4">
              <Link href="/#">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">解析</Button>
              </Link>
              <Link href="/horses">
                <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">直近の追加</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>
      
      <AnalysisContent />
    </>
  );
}
