const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // VercelではSSRを使用するため、standaloneモードを使用
  output: 'standalone',
  trailingSlash: false,

  // 環境変数の設定
  env: {
    // クライアントサイドで利用可能な環境変数
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://saraokudb.onrender.com',
    // サーバーサイドで利用可能な環境変数 - Vercel環境変数のみ使用
    API_BASE_URL: process.env.PROD_API_BASE_URL || process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL,
  },

  // ビルド対象のページ拡張子を制限
  pageExtensions: ['tsx', 'ts', 'jsx', 'js', 'mdx'],

  images: {
    unoptimized: true,
    domains: ['vercel.app', 'localhost', 'railway.app', 'up.railway.app', 'onrender.com'],
  },

  // 開発環境でのみ詳細なログを出力
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
};

module.exports = nextConfig;
