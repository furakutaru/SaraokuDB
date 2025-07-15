'use client';

import { useState, useEffect } from 'react';

export default function TestPage() {
  const [status, setStatus] = useState<string>('テスト開始...');
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    testDataFetch();
  }, []);

  const testDataFetch = async () => {
    try {
      setStatus('データを取得中...');
      const response = await fetch('/data/horses.json');
      setStatus(`レスポンスステータス: ${response.status}`);
      
      if (!response.ok) {
        setStatus(`エラー: ${response.status} - ${response.statusText}`);
        return;
      }
      
      const horseData = await response.json();
      setData(horseData);
      setStatus('データ取得成功！');
    } catch (err) {
      setStatus(`エラー: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">データ読み込みテスト</h1>
        
        <div className="bg-white p-6 rounded-lg shadow mb-6">
          <h2 className="text-xl font-semibold mb-4">ステータス</h2>
          <p className="text-lg">{status}</p>
        </div>

        {data && (
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">取得したデータ</h2>
            <div className="space-y-2">
              <p><strong>総馬数:</strong> {data.metadata?.total_horses}</p>
              <p><strong>平均価格:</strong> ¥{data.metadata?.average_price?.toLocaleString()}</p>
              <p><strong>最終更新:</strong> {data.metadata?.last_updated}</p>
              <p><strong>馬の数:</strong> {data.horses?.length}</p>
            </div>
            
            <h3 className="text-lg font-semibold mt-6 mb-4">馬一覧（最初の3頭）</h3>
            <div className="space-y-2">
              {data.horses?.slice(0, 3).map((horse: any, index: number) => (
                <div key={index} className="p-3 bg-gray-50 rounded">
                  <p><strong>名前:</strong> {horse.name}</p>
                  <p><strong>性別:</strong> {horse.sex}</p>
                  <p><strong>年齢:</strong> {horse.age}歳</p>
                  <p><strong>落札価格:</strong> ¥{horse.sold_price?.toLocaleString() || '0'}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mt-6">
          <button 
            onClick={testDataFetch}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            再テスト
          </button>
        </div>
      </div>
    </div>
  );
} 