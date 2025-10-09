import { ImgHTMLAttributes } from 'react';

/**
 * HorseImageコンポーネントのプロパティ
 */
export interface HorseImageProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'src'> {
  /** 画像のソース (URL文字列またはimage_urlプロパティを持つオブジェクト) */
  src?: string | { image_url: string } | null;
  /** 代替テキスト */
  alt?: string;
  /** 追加のクラス名 */
  className?: string;
  /** 画像URL (srcがオブジェクトの場合に使用) */
  image_url?: string;
}
