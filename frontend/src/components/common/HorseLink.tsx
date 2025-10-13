'use client';

import React from 'react';
import Link from 'next/link';

interface HorseLinkProps {
  id?: string | number;
  name?: string | null;
}

export default function HorseLink({ id, name }: HorseLinkProps) {
  const displayName = name ?? '';
  if (!id) return <span>{displayName}</span>;
  return (
    <Link href={`/horses/${id}`} className="hover:underline text-blue-700">
      {displayName}
    </Link>
  );
}
