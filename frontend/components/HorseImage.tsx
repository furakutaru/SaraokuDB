import React from 'react';

interface HorseImageProps extends Omit<React.ImgHTMLAttributes<HTMLImageElement>, 'src'> {
  src?: string;
  alt: string;
  fallbackSrc?: string;
}

const HorseImage: React.FC<HorseImageProps> = ({
  src,
  alt,
  fallbackSrc = 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9ImN1cnJlbnRDb2xvciIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiPjxwYXRoIGQ9Ik0xOCAxM2gxLjY4M2MuNTU5IDAgLjk1Mi0uNTgxIC43ODctMS4xNDNsLTEuNjUxLTQuODU0YTEuNSAxLjUgMCAwIDAtMS40MDItMS4wNDNoLTguMzE0YTEuNSAxLjUgMCAwIDAtMS40MDIgMS4wNDNsLTEuNjUgNC44NTRjLS4xNjUuNTYyLjIyOCAxLjE0My43ODcgMS4xNDNIM2ExIDEgMCAwIDAtMSAxdjhhMSAxIDAgMCAwIDEgMWgxNGExIDEgMCAwIDAgMS0xdi04YTEgMSAwIDAgMC0xLTF6Ij48L3BhdGg+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMCIgcj0iMyI+PC9jaXJjbGU+PC9zdmc+',
  className = '',
  width = 300,
  height = 200,
  ...props
}) => {
  const [imgSrc, setImgSrc] = React.useState<string>(src || fallbackSrc);
  React.useEffect(() => {
    setImgSrc(src || fallbackSrc);
  }, [src, fallbackSrc]);

  return (
    <div className="relative w-full h-full">
      <img
        src={imgSrc}
        alt={alt}
        className={`object-cover ${className}`}
        width={width}
        height={height}
        onError={() => setImgSrc(fallbackSrc)}
        {...props}
      />
    </div>
  );
};

export default HorseImage;
