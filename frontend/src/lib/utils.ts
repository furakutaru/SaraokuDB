import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** API ベース URL を返す */
export function getApiBase(): string {
  // 環境変数が設定されている場合はそれを使用
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // 本番環境（Vercel）でのフォールバック
  if (typeof window !== 'undefined' && window.location.hostname === 'saraoku-db.vercel.app') {
    return 'https://saraokudb.onrender.com';
  }
  
  // 開発環境や同一起源の場合は相対パスを使用するために空文字を返す
  return '';
}
