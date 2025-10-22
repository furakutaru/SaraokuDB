import type { Metadata } from "next";
import { Inter } from 'next/font/google';
import './globals.css';

// If loading a variable font, you don't need to specify the font weight
const inter = Inter({ subsets: ['latin'] })

// ビューポート設定を分離
export const viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
};

export const metadata: Metadata = {
  title: "サラオクDB | サラブレッドオークション データベース",
  description: "楽天サラブレッドオークションのデータをスクレイピングし、統計情報と馬の詳細情報を表示するWebアプリケーション",
  keywords: "サラブレッド,オークション,競馬,馬,データベース",
  authors: [{ name: "サラオクDB" }],
  robots: "noindex, nofollow",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body
        className={`${inter.className} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
