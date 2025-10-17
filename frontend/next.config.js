/** @type {import('next').NextConfig} */
const nextConfig = {
  // VercelではSSRを使用するため、standaloneモードを使用
  output: 'standalone',
  trailingSlash: true,
  images: {
    unoptimized: true,
    domains: ['vercel.app'],
  },
  // 環境変数の設定
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // リライト設定
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
