/** @type {import('next').NextConfig} */
const nextConfig = {
  // 開発時は静的エクスポートを無効にする
  // 本番デプロイ時のみ有効にする場合は環境変数で制御
  ...(process.env.NODE_ENV === 'production' && {
    output: 'export',
    trailingSlash: true,
    images: {
      unoptimized: true,
    },
  }),
  
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