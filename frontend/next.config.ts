import type { NextConfig } from "next";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8001';

const nextConfig: NextConfig = {
  // 環境変数をクライアントサイドで利用可能にする
  env: {
    NEXT_PUBLIC_API_BASE_URL: API_BASE_URL,
  },
  
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${API_BASE_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
