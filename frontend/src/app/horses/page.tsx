'use client'

import { useEffect, useState } from 'react'

interface Horse {
  id: number
  name: string
  sex?: string
  age?: number
  latest_auction?: {
    price?: number
    auction_date?: string
    // 他の必要なフィールドを追加
  }
}

// 並べ替えオプションの型
type SortOption = 'price_desc' | 'price_asc' | 'name_asc' | 'name_desc'

export default function HorsesPage() {
  const [horses, setHorses] = useState<Horse[]>([])
  const [sortBy, setSortBy] = useState<SortOption>('price_desc') // デフォルトは価格の降順
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshKey, setRefreshKey] = useState(0) // リロード用のキー

  useEffect(() => {
    const fetchHorses = async () => {
      setIsLoading(true)
      setError(null)
      try {
        console.log(`Fetching horses with sort: ${sortBy}`);
        const response = await fetch(`/api/horses?sort=${sortBy}`, {
          cache: 'no-store', // キャッシュを無効化
          next: { revalidate: 0 } // 必ず最新のデータを取得
        });
        
        if (!response.ok) {
          const errorData = await response.text();
          console.error('Error response:', errorData);
          throw new Error(`データの取得に失敗しました (${response.status})`);
        }
        
        const data = await response.json();
        console.log('Received data:', data);
        
        // バックエンドのレスポンス形式に合わせて調整
        setHorses(Array.isArray(data) ? data : (data.horses || []));
      } catch (err: unknown) {
        console.error('Error fetching horses:', err);
        const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';
        setError(`データの読み込み中にエラーが発生しました: ${errorMessage}`);
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchHorses();
  }, [sortBy, refreshKey]); // refreshKeyが変更されたときも再取得

  // 価格をフォーマットするヘルパー関数
  const formatPrice = (price?: number) => {
    if (price === undefined || price === null || price === 0) return '非公開';
    return new Intl.NumberFormat('ja-JP').format(price) + '円';
  };
  
  // デバッグ用: 馬のデータをログに出力
  useEffect(() => {
    if (horses.length > 0) {
      console.log('Horses data with auction info:', horses.map(horse => ({
        id: horse.id,
        name: horse.name,
        latest_auction: horse.latest_auction
      })));
    }
  }, [horses]);

  // 日付をフォーマットするヘルパー関数
  const formatDate = (dateString?: string) => {
    if (!dateString) return '不明'
    const date = new Date(dateString)
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  if (isLoading) {
    return (
      <div className="container mx-auto p-4">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4" role="alert">
          <p className="font-bold">エラーが発生しました</p>
          <p>{error}</p>
          <button 
            onClick={() => window.location.reload()}
            className="mt-2 bg-red-500 hover:bg-red-700 text-white font-bold py-1 px-4 rounded"
          >
            再読み込み
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 gap-4">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-800">馬一覧</h1>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2">
          <label htmlFor="sort" className="text-sm font-medium text-gray-700 whitespace-nowrap">
            並べ替え:
          </label>
          <select
            id="sort"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortOption)}
            className="block w-full md:w-48 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            <option value="price_desc">価格の高い順</option>
            <option value="price_asc">価格の安い順</option>
            <option value="name_asc">名前順 (A-Z)</option>
            <option value="name_desc">名前順 (Z-A)</option>
          </select>
        </div>
      </div>
      
      {horses.length === 0 ? (
        <div className="text-center py-12">
          <p className="text-gray-500">表示する馬の情報がありません</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          {horses.map((horse) => (
            <div 
              key={horse.id} 
              className="bg-white border border-gray-200 rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-200"
            >
              <div className="p-4">
                <h2 className="text-xl font-semibold text-gray-800 mb-2">{horse.name || '名前不明'}</h2>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center">
                    <span className="w-20 text-gray-500">性別:</span>
                    <span>{horse.sex || '不明'}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-20 text-gray-500">年齢:</span>
                    <span>{horse.age !== undefined ? `${horse.age}歳` : '不明'}</span>
                  </div>
                  {horse.latest_auction && (
                    <>
                      <div className="flex items-center">
                        <span className="w-20 text-gray-500">落札価格:</span>
                        <span className={`font-medium ${horse.latest_auction?.price ? 'text-blue-600' : 'text-gray-500'}`}>
                          {formatPrice(horse.latest_auction?.price)}
                        </span>
                      </div>
                      <div className="flex items-center">
                        <span className="w-20 text-gray-500">落札日:</span>
                        <span>{formatDate(horse.latest_auction.auction_date)}</span>
                      </div>
                    </>
                  )}
                </div>
                
                <div className="mt-4 pt-3 border-t border-gray-100">
                  <a 
                    href={`/horses/${horse.id}`}
                    className="text-sm font-medium text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    詳細を見る →
                  </a>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
