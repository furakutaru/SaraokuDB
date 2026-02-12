import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** API ベース URL を返す */
export function getApiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'https://saraokudb.onrender.com';
}
