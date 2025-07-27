import { useState } from 'react';
import Image from 'next/image';

interface HorseImageProps {
  src: string;
  alt: string;
  className?: string;
  width?: number;
  height?: number;
}

export default function HorseImage({ 
  src, 
  alt, 
  className = '',
  width = 300,
  height = 300 
}: HorseImageProps) {
  const [imgSrc, setImgSrc] = useState(src);
  const [isLoading, setIsLoading] = useState(true);

  return (
    <div className={`relative ${className}`} style={{ width: '100%', height: '100%' }}>
      <Image
        src={imgSrc}
        alt={alt}
        width={width}
        height={height}
        className={`transition-opacity duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
        onLoadingComplete={() => setIsLoading(false)}
        onError={() => {
          setImgSrc('/placeholder-horse.jpg');
          setIsLoading(false);
        }}
        loading="lazy"
        unoptimized={process.env.NODE_ENV !== 'production'}
      />
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="animate-pulse text-gray-400">読み込み中...</div>
        </div>
      )}
    </div>
  );
}