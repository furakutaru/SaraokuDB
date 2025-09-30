import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'サラオクDB | 直近の追加',
  description: '直近追加されたサラブレッドの一覧を表示します。',
};

export default function HorsesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {children}
    </div>
  );
}
