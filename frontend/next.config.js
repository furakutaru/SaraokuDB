/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: false, // Strict Modeを無効化
  swcMinify: true,
  images: {
    domains: ['localhost'],
    unoptimized: true,
  },
  poweredByHeader: false,
  
  // APIリライト設定
  async rewrites() {
    return [
      {
        source: '/api/horses/:id*',
        destination: 'http://localhost:8001/api/horses/:id*',
      },
      {
        source: '/api/:path*',
        destination: 'http://localhost:8001/api/:path*',
      }
    ];
  },
  
  // キャッシュ設定
  onDemandEntries: {
    maxInactiveAge: 25 * 1000, // 25秒
    pagesBufferLength: 2,
  },
  
  // ヘッダー設定
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          { key: 'Access-Control-Allow-Credentials', value: 'true' },
          { key: 'Access-Control-Allow-Origin', value: '*' },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS' },
          { key: 'Access-Control-Allow-Headers', value: 'X-Requested-With, Content-Type' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;