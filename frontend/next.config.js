/** @type {import('next').NextConfig} */
const path = require('path');

// バックエンドのAPIベースURL
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig = {
  // 静的エクスポート(output: 'export')はVercel運用では不要なので削除
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // Webpackのエイリアス設定
  webpack: (config) => {
    config.resolve.alias['@'] = path.resolve(__dirname, 'src');
    return config;
  },
  // 環境変数をクライアントサイドで利用可能に
  env: {
    NEXT_PUBLIC_API_URL: API_BASE_URL,
  },
  // リライト設定（開発時のみ）
  ...(process.env.NODE_ENV !== 'production' && {
    async rewrites() {
      return [
        // 既存のリライトルールを保持
        {
          source: '/horses.json',
          destination: '/data/horses.json',
        },
        // バックエンドAPIへのプロキシ設定
        {
          source: '/api/:path*',
          destination: `${API_BASE_URL}/:path*`,
        },
      ];
    },
  }),
};

module.exports = nextConfig;