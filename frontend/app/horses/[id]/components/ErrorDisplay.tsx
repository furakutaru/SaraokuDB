'use client';

import React from 'react';
import { Typography, Button } from '@mui/material';
import Link from 'next/link';

interface ErrorMessageProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorMessage({ message, onRetry }: ErrorMessageProps) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1, color: 'text-red-600' }}>エラー</Typography>
        <p className="text-gray-700 mb-6">{message}</p>
        <div className="flex justify-center gap-4">
          <Button component={Link} href="/">
            トップに戻る
          </Button>
          {onRetry && (
            <Button variant="outlined" onClick={onRetry}>
              再試行
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}

interface SimpleErrorProps {
  message: string;
}

export function SimpleError({ message }: SimpleErrorProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full text-center">
        <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1, color: 'text-red-600' }}>エラーが発生しました</Typography>
        <p className="mb-6">{message}</p>
        <a 
          href="/" 
          className="inline-block bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 transition-colors"
        >
          トップに戻る
        </a>
      </div>
    </div>
  );
}
