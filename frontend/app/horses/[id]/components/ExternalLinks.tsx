'use client';

interface ExternalLinksProps {
  jbisUrl?: string;
  auctionUrl?: string;
  rakutenUrl?: string;
  className?: string;
}

export default function ExternalLinks({ 
  jbisUrl, 
  auctionUrl,
  rakutenUrl,
  className = '' 
}: ExternalLinksProps) {
  // デバッグ用
  console.log('ExternalLinks - jbisUrl:', jbisUrl);
  console.log('ExternalLinks - auctionUrl:', auctionUrl);
  console.log('ExternalLinks - rakutenUrl:', rakutenUrl);
  console.log('ExternalLinks - props:', { jbisUrl, auctionUrl, rakutenUrl, className });

  // すべてのURLが空の場合は何も表示しない
  if (!jbisUrl && !auctionUrl && !rakutenUrl) {
    console.log('No URLs to display');
    return null;
  }

  return (
    <div className={`mt-2 flex flex-wrap gap-4 ${className}`}>
      {jbisUrl && (
        <a 
          href={jbisUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
          onClick={(e) => {
            e.stopPropagation();
            if (!jbisUrl) {
              e.preventDefault();
            }
          }}
        >
          JBIS
        </a>
      )}
      {auctionUrl && (
        <a
          href={auctionUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
          onClick={(e) => {
            e.stopPropagation();
            if (!auctionUrl) {
              e.preventDefault();
            }
          }}
        >
          サラオク
        </a>
      )}
      {rakutenUrl && (
        <a
          href={rakutenUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
          onClick={(e) => {
            e.stopPropagation();
            if (!rakutenUrl) {
              e.preventDefault();
            }
          }}
        >
          楽天
        </a>
      )}
    </div>
  );
}
