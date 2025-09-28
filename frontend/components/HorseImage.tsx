import React from 'react';
import Image, { ImageProps } from 'next/image';

interface HorseImageProps extends Omit<ImageProps, 'src' | 'alt'> {
  src?: string | null;
  alt: string;
  fallbackSrc?: string;
}

const HorseImage: React.FC<HorseImageProps> = ({
  src,
  alt,
  fallbackSrc = '/images/horse-placeholder.png',
  ...props
}) => {
  const [imgSrc, setImgSrc] = React.useState<string>(src || fallbackSrc);

  React.useEffect(() => {
    setImgSrc(src || fallbackSrc);
  }, [src, fallbackSrc]);

  return (
    <Image
      {...props}
      src={imgSrc}
      alt={alt}
      onError={() => setImgSrc(fallbackSrc)}
    />
  );
};

export default HorseImage;
