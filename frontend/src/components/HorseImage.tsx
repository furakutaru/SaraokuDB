import React from 'react';

interface HorseImageProps {
  src: string | null;
  alt: string;
  width?: number | string;
  height?: number | string;
  className?: string;
}

const HorseImage: React.FC<HorseImageProps> = ({
  src,
  alt,
  width = 200,
  height = 200,
  className = '',
}) => {
  if (!src) {
    return (
      <div 
        className={`bg-gray-200 flex items-center justify-center ${className}`}
        style={{ width, height }}
      >
        <span className="text-gray-500">No Image</span>
      </div>
    );
  }

  return (
    <div className={`${className}`} style={{ width, height, overflow: 'hidden' }}>
      <img
        src={src}
        alt={alt}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
        loading="lazy"
      />
    </div>
  );
};

export default HorseImage;
