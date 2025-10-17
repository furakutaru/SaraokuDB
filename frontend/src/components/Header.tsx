import Link from 'next/link';
import { Button } from '@/components/ui/button';

interface HeaderProps {
  pageTitle: string;
}

export function Header({ pageTitle }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b sticky top-0 z-10">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center gap-4">
            <h1 className="text-2xl font-bold text-gray-900">{pageTitle}</h1>
          </div>
          <div className="flex gap-4">
            <Link href="/">
              <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">解析</Button>
            </Link>
            <Link href="/horses">
              <Button variant="outline" className="rounded-md bg-white border border-black text-black hover:bg-gray-100">直近の追加</Button>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
