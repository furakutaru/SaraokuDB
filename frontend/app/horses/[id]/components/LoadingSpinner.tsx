'use client';

import React from 'react';

interface LoadingSpinnerProps {
  fullScreen?: boolean;
  className?: string;
}

export function LoadingSpinner({ 
  fullScreen = true,
  className = '' 
}: LoadingSpinnerProps) {
  const containerClasses = fullScreen 
    ? 'min-h-screen bg-gray-50 flex items-center justify-center' 
    : 'flex items-center justify-center';

  return (
    <div className={`${containerClasses} ${className}`}>
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
    </div>
  );
}

interface SimpleLoadingProps {
  message?: string;
  className?: string;
}

export function SimpleLoading({ 
  message = '読み込み中...',
  className = '' 
}: SimpleLoadingProps) {
  return (
    <div className={`flex items-center justify-center space-x-2 ${className}`}>
      <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-primary"></div>
      {message && <span className="text-sm text-gray-600">{message}</span>}
    </div>
  );
}

export default LoadingSpinner;
