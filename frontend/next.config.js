const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  // VercelではSSRを使用するため、standaloneモードを使用
  output: 'standalone',
  trailingSlash: false,

  // 環境変数の設定
  env: {
    // クライアントサイドで利用可能な環境変数
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
    // サーバーサイドで利用可能な環境変数 - Vercel環境変数のみ使用
    API_BASE_URL: process.env.PROD_API_BASE_URL || process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_URL,
  },

  // ビルド対象のページ拡張子を制限
  pageExtensions: ['tsx', 'ts', 'jsx', 'js', 'mdx'],

  // ビルドから除外するパスの設定
  webpack: (config, { isServer }) => {
    // 環境変数をクライアントサイドで利用可能にする
    config.plugins.push(
      new (require('webpack')).DefinePlugin({
        'process.env.STATIC_FILES_DIR': JSON.stringify(path.resolve(__dirname, '../static-frontend/public')),
        'process.env.NEXT_PUBLIC_API_URL': JSON.stringify(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001')
      })
    );

    // バックアップディレクトリとバックアップファイルを除外するルール
    config.module.rules.push({
      test: /([/\\])(app_backup\\.disabled|_backup|backup_|_backup_|app_backup_|__horses_backup_|\\.bak|\\.backup)([/\\]|$)/,
      use: 'null-loader'
    });

    // ビルドから除外するパスを明示的に指定
    config.plugins.push(
      new (require('webpack')).IgnorePlugin({
        checkResource: function (resource) {
          // バックアップ関連のファイルを除外
          const isBackupFile = /(^|[\\/])(app_backup\\.disabled|_backup|backup_|_backup_|app_backup_|__horses_backup_|\\.bak|\\.backup)([\\/]|$)/.test(resource);
          if (isBackupFile) {
            console.log('Excluding backup file from build:', resource);
            return true;
          }
          return false;
        }
      })
    );

    // ビルドから除外するパスを明示的に指定（Next.js 13+用）
    if (config.resolve) {
      config.resolve.alias = {
        ...config.resolve.alias,
        // バックアップディレクトリを無効化
        'app_backup.disabled': false,
        '_backup': false,
        'backup_': false,
        '_backup_': false,
        'app_backup_': false,
        '__horses_backup_': false,
        // パスエイリアスの設定
        '@': require('path').resolve(__dirname, 'src')
      };
    }

    return config;
  },

  images: {
    unoptimized: true,
    domains: ['vercel.app', 'localhost'],
  },

  // リライト設定 (ローカルAPIルートを使用するため、一旦コメントアウト)
  /*
  async rewrites() {
    const apiUrl = 'http://localhost:8001';  // ポートを8001に固定
    console.log('Setting up rewrites with API URL:', apiUrl);
    
    return [
      // APIリクエストをバックエンドにプロキシ
      {
        source: '/api/:path*',
        destination: `${apiUrl}/api/:path*`,  // /api パスを追加
      },
    ];
  },
  */

  // 開発環境でのみ詳細なログを出力
  logging: {
    fetches: {
      fullUrl: true,
    },
  },
};

module.exports = nextConfig;
