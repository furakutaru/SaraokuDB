'use client';

interface ExternalLinksProps {
  jbisUrl?: string | null;
  auctionUrl?: string | null;
  className?: string;
}

export default function ExternalLinks({ 
  jbisUrl, 
  auctionUrl,
  className = '' 
}: ExternalLinksProps) {
  // 有効なURLがあるかチェック（null, undefined, 空文字列を除外）
  const hasValidJbisUrl = jbisUrl != null && jbisUrl.trim() !== '';
  const hasValidAuctionUrl = auctionUrl != null && auctionUrl.trim() !== '';

  // すべてのURLが無効の場合は何も表示しない
  if (!hasValidJbisUrl && !hasValidAuctionUrl) {
    return null;
  }

  return (
    <div className={`mt-2 flex flex-wrap gap-4 ${className}`}>
      {hasValidJbisUrl && (
        <a 
          href={jbisUrl!} 
          target="_blank" 
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          JBIS
        </a>
      )}
      {hasValidAuctionUrl && (
        <a
          href={auctionUrl!}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
          onClick={(e) => e.stopPropagation()}
        >
          サラオク
        </a>
      )}
    </div>
  );
}
