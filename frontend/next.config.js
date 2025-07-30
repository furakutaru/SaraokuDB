/** @type {import('next').NextConfig} */
const path = require('path');

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
  // リライト設定（開発時のみ）
  ...(process.env.NODE_ENV !== 'production' && {
    async rewrites() {
      return [
        {
          source: '/horses.json',
          destination: '/data/horses.json',
        },
        {
          source: '/api/horses/:path*',
          destination: 'http://localhost:3002/api/horses/:path*',
        },
      ];
    },
  }),
};

module.exports = nextConfig;