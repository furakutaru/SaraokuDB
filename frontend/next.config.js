/** @type {import('next').NextConfig} */
const nextConfig = {
  // VercelではSSRを使用するため、standaloneモードを使用
  output: 'standalone',
  trailingSlash: true,
  // ビルド対象のページ拡張子を制限
  pageExtensions: ['tsx', 'ts', 'jsx', 'js', 'mdx'],
  
  // ビルドから除外するパスの設定
  webpack: (config, { isServer }) => {
    // バックアップディレクトリとバックアップファイルを除外するルール
    config.module.rules.push({
      test: /([/\\])(app_backup\.disabled|_backup|backup_|_backup_|app_backup_|__horses_backup_|\.bak|\.backup)([/\\]|$)/,
      use: 'null-loader'
    });
    
    // ビルドから除外するパスを明示的に指定
    config.plugins.push(
      new (require('webpack')).IgnorePlugin({
        checkResource: function(resource) {
          // バックアップ関連のファイルを除外
          const isBackupFile = /(^|[\\/])(app_backup\.disabled|_backup|backup_|_backup_|app_backup_|__horses_backup_|\.bak|\.backup)([\\/]|$)/.test(resource);
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
