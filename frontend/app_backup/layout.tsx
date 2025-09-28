import React from 'react';
import type { Metadata } from "next";
import { Inter } from 'next/font/google';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Container } from '@mui/material';
import './globals.css';

// If loading a variable font, you don't need to specify the font weight
const inter = Inter({ subsets: ['latin'] });

// MUIテーマの設定
const theme = createTheme({
  palette: {
    mode: 'light', // または 'dark' を選択
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

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
      <body className={`${inter.className} antialiased`}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <Container component="main" sx={{ mt: 4, mb: 4, flex: 1 }}>
              {children}
            </Container>
          </Box>
        </ThemeProvider>
      </body>
    </html>
  );
}
