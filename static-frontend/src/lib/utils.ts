import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** 末尾のスラッシュを除去した API ベース URL を返す */
export function getApiBase(): string {
  const base =
    process.env.NEXT_PUBLIC_PROD_API_BASE_URL ||
    process.env.NEXT_PUBLIC_API_BASE ||
    "http://localhost:8001";
  return base.replace(/\/+$/, "");
}
