/** @type {import('next').NextConfig} */
const nextConfig = {
  // 静的エクスポート(output: 'export')はVercel運用では不要なので削除
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  // リライト設定（開発時のみ）
  ...(process.env.NODE_ENV !== 'production' && {
    async rewrites() {
      return [
        {
          source: '/horses.json',
          destination: '/data/horses.json',
        },
      ];
    },
  }),
};

module.exports = nextConfig; 