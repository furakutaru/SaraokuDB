import { useState } from 'react';
import Image from 'next/image';

interface HorseImageProps {
  src?: string;
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
    <div className={`relative ${className}`}>
      <Image
        src={imgSrc || '/images/horse-placeholder.png'}
        alt={alt}
        width={width}
        height={height}
        className={`transition-opacity duration-300 ${isLoading ? 'opacity-0' : 'opacity-100'}`}
        onLoad={() => setIsLoading(false)}
        onError={() => setImgSrc('/images/horse-placeholder.png')}
        priority
      />
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse rounded-md">
          <div className="w-full h-full flex items-center justify-center">
            <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        </div>
      )}
    </div>
  );
}