/** @type {import('next').NextConfig} */
const path = require('path');
const webpack = require('webpack');

const nextConfig = {
  reactStrictMode: false, // Strict Modeを無効化
  swcMinify: true,
  compiler: {
    emotion: true,
  },
  images: {
    domains: ['localhost'],
    unoptimized: true,
  },
  poweredByHeader: false,
  
  // サーバーコンポーネントで使用する外部パッケージ
  experimental: {
    serverComponentsExternalPackages: ['@emotion/react', '@emotion/styled'],
  },
  
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
  
  // Webpack の設定
  webpack: (config, { isServer }) => {
    // エイリアス設定
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
      // エイリアスの追加
      '@/src': path.resolve(__dirname, 'src'),
      '@/components': path.resolve(__dirname, 'src/components'),
      '@/utils': path.resolve(__dirname, 'src/utils'),
    };

    // ビルドから除外するディレクトリ
    config.module.rules.push({
      test: /\.(js|jsx|ts|tsx)$/,
      exclude: [
        // テスト関連
        /node_modules\/.*\/__tests__\//,
        /node_modules\/.*\/test\//,
        /.*\/__tests__\/.*/,
        /.*\/test\/.*/,
        
        // バックアップ関連
        /.*[\/\\]([Bb]ackup|[Bb]ackups|[Aa]rchive|[Oo]ld)[\/\\].*/,
        /.*[\/\\]_?[Bb]ackup[\/\\].*/,
        /.*[\/\\].*[Bb]ackup.*[\/\\].*/,
        /.*[\/\\][^\/\\]*[Bb]ackup[^\/\\]*[\/\\].*/,
        
        // 日付付きバックアップ
        /.*[\/\\].*_backup_\d{8}_\d+[\/\\].*/i,
        /.*[\/\\].*backup_\d{8}_\d+[\/\\].*/i,
        /.*[\/\\]backup[\/\\].*_\d+[\/\\].*/i,
        
        // 特定のバックアップディレクトリ
        /.*[\/\\]app_backup[\/\\].*/i,
        /.*[\/\\]scripts_backup_[^\/\\]+[\/\\].*/i,
        /.*[\/\\]horses_backup_[^\/\\]+[\/\\].*/i,
        /.*[\/\\]_backup_[^\/\\]+[\/\\].*/i,
      ],
    });

    // バックアップディレクトリを無視するプラグインを追加
    config.plugins.push(
      new webpack.IgnorePlugin({
        resourceRegExp: /^.*[\/\\]([Bb]ackup|[Bb]ackups|[Aa]rchive|[Oo]ld|_?backup_?|.*[Bb]ackup.*)[\/\\].*$/
      })
    );
    
    // デバッグ用に除外されたファイルをログに出力
    if (!isServer) {
      config.plugins.push(
        new webpack.NormalModuleReplacementPlugin(
          /^.*[\/\\]([Bb]ackup|[Bb]ackups|[Aa]rchive|[Oo]ld|_?backup_?|.*[Bb]ackup.*)[\/\\].*/,
          (resource) => {
            console.warn('Excluded from build:', resource.request);
            resource.request = './empty-module.js';
          }
        )
      );
    }

    return config;
  },

  // ビルド時の型チェックを無効化
  typescript: {
    ignoreBuildErrors: true,
  },
  
  // ビルド時のESLintチェックを無効化
  eslint: {
    ignoreDuringBuilds: true,
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