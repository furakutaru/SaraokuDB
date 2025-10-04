import React from 'react';
import { Metadata } from 'next';

type HorsesLayoutProps = {
  children: React.ReactNode;
};

export const metadata: Metadata = {
  title: 'サラオクDB | 直近の追加',
  description: '直近追加されたサラブレッドの一覧を表示します。',
};

export default function HorsesLayout({
  children,
}: HorsesLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      {children}
    </div>
  );
}
