import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** API ベース URL を返す */
export function getApiBase(): string {
  // 開発環境や同一起源の場合は相対パスを使用するために空文字を返す
  return process.env.NEXT_PUBLIC_API_URL || '';
}
