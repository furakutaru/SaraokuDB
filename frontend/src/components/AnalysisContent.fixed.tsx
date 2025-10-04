'use client';

import { useEffect, useState } from 'react';

// シンプルなコンポーネントに置き換え
export default function AnalysisContent() {
  const [message, setMessage] = useState('Loading...');

  useEffect(() => {
    setMessage('Analysis Content Loaded');
  }, []);

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Horse Analysis</h1>
      <p>{message}</p>
    </div>
  );
}
