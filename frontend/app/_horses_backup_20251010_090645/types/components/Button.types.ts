import { ButtonHTMLAttributes } from 'react';

/**
 * ボタンのバリアントタイプ
 */
export type ButtonVariant = 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';

/**
 * Buttonコンポーネントのプロパティ
 */
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** 子要素 */
  children: React.ReactNode;
  /** 追加のクラス名 */
  className?: string;
  /** ボタンのスタイルバリアント */
  variant?: ButtonVariant;
}
