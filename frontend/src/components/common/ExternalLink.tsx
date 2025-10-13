'use client';

import React from 'react';

interface ExternalLinkProps {
  href?: string | null;
  label: string;
  className?: string;
  title?: string;
}

export default function ExternalLink({ href, label, className, title }: ExternalLinkProps) {
  if (!href) return null;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={className} title={title}>
      {label}
    </a>
  );
}
