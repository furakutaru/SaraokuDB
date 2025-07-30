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
      
      // horses.json を取得
      const horsesResponse = await fetch('/data/horses.json');
      if (!horsesResponse.ok) {
        setStatus(`エラー: horses.json の取得に失敗 - ${horsesResponse.status} ${horsesResponse.statusText}`);
        return;
      }
      
      // auction_history.json を取得
      const auctionHistoryResponse = await fetch('/data/auction_history.json');
      if (!auctionHistoryResponse.ok) {
        setStatus(`エラー: auction_history.json の取得に失敗 - ${auctionHistoryResponse.status} ${auctionHistoryResponse.statusText}`);
        return;
      }
      
      const horses = await horsesResponse.json();
      const auctionHistory = await auctionHistoryResponse.json();
      
      // データをマージ
      const mergedData = {
        horses: horses,
        auctionHistory: auctionHistory,
        metadata: {
          last_updated: new Date().toISOString(),
          total_horses: horses.length,
          total_auctions: auctionHistory.length
        }
      };
      
      setData(mergedData);
      setStatus('データの取得とマージが完了しました！');
    } catch (err) {
      setStatus(`エラー: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  // 落札価格表示用関数を追加
  const formatPrice = (price: number | null | undefined) => {
    if (price === null || price === undefined) return '-';
    return '¥' + price.toLocaleString();
  };

  // 賞金表示用関数（もし存在すれば）
  const formatPrize = (val: number | null | undefined) => {
    if (val === null || val === undefined) return '-';
    return `${val.toFixed(1)}万円`;
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
          <div className="space-y-6">
            {/* メタデータ表示 */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">メタデータ</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <p><strong>馬の総数:</strong> {data.metadata?.total_horses || 0}</p>
                  <p><strong>オークション履歴の総数:</strong> {data.metadata?.total_auctions || 0}</p>
                </div>
                <div>
                  <p><strong>最終更新日時:</strong> {new Date(data.metadata?.last_updated).toLocaleString()}</p>
                </div>
              </div>
            </div>

            {/* 馬一覧 */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">馬一覧（最初の3頭）</h2>
              {data.horses && data.horses.length > 0 ? (
                <div className="space-y-2">
                  {data.horses.slice(0, 3).map((horse: any) => (
                    <div key={horse.id} className="p-4 border rounded-lg hover:bg-gray-50">
                      <h3 className="font-semibold text-lg">{horse.name} (ID: {horse.id})</h3>
                      <div className="grid grid-cols-2 gap-2 mt-2">
                        <p><span className="text-gray-600">性別・年齢:</span> {horse.sex || '-'} {horse.age || ''}歳</p>
                        <p><span className="text-gray-600">父:</span> {horse.sire || '-'}</p>
                        <p><span className="text-gray-600">母:</span> {horse.dam || '-'}</p>
                        <p><span className="text-gray-600">母父:</span> {horse.damsire || '-'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p>馬のデータがありません</p>
              )}
            </div>

            {/* オークション履歴 */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h2 className="text-xl font-semibold mb-4">オークション履歴（最新3件）</h2>
              {data.auctionHistory && data.auctionHistory.length > 0 ? (
                <div className="space-y-2">
                  {data.auctionHistory.slice(0, 3).map((auction: any, index: number) => (
                    <div key={index} className="p-4 border rounded-lg">
                      <p><strong>馬ID:</strong> {auction.horse_id}</p>
                      <p><strong>オークション日:</strong> {auction.auction_date}</p>
                      <p><strong>落札価格:</strong> {formatPrice(auction.sold_price)}</p>
                      <p><strong>売り主:</strong> {auction.seller || '不明'}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p>オークション履歴がありません</p>
              )}
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