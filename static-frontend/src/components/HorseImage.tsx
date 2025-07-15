interface HorseImageProps {
  src: string;
  alt: string;
  className?: string;
}

export default function HorseImage({ src, alt, className }: HorseImageProps) {
  return (
    <img
      src={src}
      alt={alt}
      className={className}
    />
  );
} 