'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ExternalLink } from 'lucide-react';
import { formatPrize } from '@/utils/format';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { UnifiedHorse, AuctionHistory } from '@/types/unifiedHorse';
import { Header } from '@/components/Header';

// コンポーネント用の型
type Horse = Omit<UnifiedHorse, 'basic_info' | 'auction_history'> & {
  // 基本情報をトップレベルに展開
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  // メタデータ
  metadata: {
    created_at: string;
    updated_at: string;
    data_source: string;
  };
  color?: string;
  birthday?: string;
  image_url?: string;
  jbis_url?: string;
  auction_url?: string;
  is_retired?: boolean;
  retirement_date?: string;

  // レース成績（統合済み）
  unified_race_records?: {
    total_races: number;
    wins: number;
    record_format?: string;
    formatted_record?: string;
    total_prize_money: number;
    last_race_date?: string;
    last_prize_update?: string;
  };

  // オークション情報
  latest_auction?: AuctionHistory | null;
  auction_history?: AuctionHistory[];
}

// 馬詳細ページのプロパティ型
interface HorseDetailPageProps {
  params: {
    id: string;
  };
}

// 馬詳細コンテンツのプロパティ型
interface HorseDetailContentProps {
  horse: UnifiedHorse;
  auctionHistory: AuctionHistory | null;
  isPreview?: boolean;
}

// --- ヘルパー関数 ---
const calculateGrowthRate = (start: number, latest: number): string => {
  if (start === 0) return latest > 0 ? '∞' : '0';
  return (((latest - start) / start) * 100).toFixed(1);
};

const formatDate = (dateInput: string | string[] | undefined): string => {
  if (!dateInput) return '-';

  try {
    // 配列の場合は最初の要素を使用
    const dateStr = Array.isArray(dateInput) ? dateInput[0] : dateInput;

    // 日付としてパース可能な形式であればフォーマット
    if (dateStr && typeof dateStr === 'string' && dateStr.match(/^\d{4}-\d{2}-\d{2}/)) {
      return format(parseISO(dateStr), 'yyyy年MM月dd日', { locale: ja });
    }

    return dateStr || '-';
  } catch (e) {
    console.warn('Failed to format date:', dateInput, e);
    return String(dateInput || '-');
  }
};

const formatPrice = (price: number | string | null | undefined): string => {
  if (price === null || price === undefined) return '-';
  if (typeof price === 'string') {
    // 数値に変換可能な場合は変換
    const num = parseFloat(price.replace(/[^0-9.-]+/g, ''));
    if (!isNaN(num)) {
      return `¥${num.toLocaleString()}`;
    }
    return price;
  }
  return `¥${price.toLocaleString()}`;
};


// 落札価格を表示する関数
const displayPrice = (horse: Horse, auctionHistory: AuctionHistory | null | undefined) => {
  // 未出走の場合は「未出走」を返す
  if (horse.race_records?.total_races === 0) {
    return '未出走';
  }

  // オークション履歴から価格を取得
  if (auctionHistory) {
    if (auctionHistory.is_unsold) {
      return '主取り';
    }

    if (auctionHistory.price) {
      const priceInMan = auctionHistory.price / 10000;
      return `${priceInMan.toLocaleString()}万円`;
    }
  }

  // 馬の直接のsold_priceをチェック
  if (horse.sold_price) {
    const priceInMan = horse.sold_price / 10000;
    return `${priceInMan.toLocaleString()}万円`;
  }

  // いずれも見つからない場合
  return '-';
};

// --- コンポーネント ---
const HorseDetailPage = ({ params }: HorseDetailPageProps) => {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [horse, setHorse] = useState<Horse | null>(null);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory | null>(null);


  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        setIsLoading(true);
        // 環境変数に基づいてAPI URLを決定
        const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const FINAL_API_BASE_URL = process.env.PROD_API_BASE_URL || API_BASE_URL;
        const API_URL = `${FINAL_API_BASE_URL}/api`;
        
        // デバッグログ
        console.log(`[HorseDetail] API_BASE_URL: ${API_BASE_URL}`);
        console.log(`[HorseDetail] FINAL_API_BASE_URL: ${FINAL_API_BASE_URL}`);
        console.log(`[HorseDetail] API_URL: ${API_URL}`);
        console.log(`[HorseDetail] NODE_ENV: ${process.env.NODE_ENV}`);
        
        // バックエンドAPIからデータを取得
        if (process.env.PROD_API_BASE_URL) {
          const backendUrl = `${API_URL}/horses/${params.id}`;
          console.log(`[HorseDetail] Fetching from backend: ${backendUrl}`);
          
          const response = await fetch(backendUrl, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
            redirect: 'follow'
          });

          if (!response.ok) {
            throw new Error(`バックエンドAPIエラー: ${response.status}`);
          }

          const horseData = await response.json();
          
          if (!horseData) {
            throw new Error('バックエンドAPIからデータが取得できませんでした');
          }

          // APIデータをフロントエンド形式に変換
          const processedHorse: Horse = {
            ...horseData,
            // 基本情報をトップレベルに展開
            name: horseData.name || '',
            sex: horseData.sex || '',
            age: horseData.age || 0,
            sire: horseData.sire || '',
            dam: horseData.dam || '',
            damsire: horseData.dam_sire || horseData.damsire || '',
            // メタデータ
            metadata: {
              created_at: horseData.created_at || new Date().toISOString(),
              updated_at: horseData.updated_at || new Date().toISOString(),
              data_source: horseData.data_source || 'api'
            },
            // レコード情報
            race_record: horseData.race_record || horseData.race_records || {
              total_races: 0,
              wins: 0,
              total_prize_money: 0
            },
            // オークション情報
            latest_auction: horseData.latest_auction || null,
            auction_history: horseData.auction_history || [],
            // 履歴データをhistory形式に変換
            history: horseData.auction_history || []
          };

          setHorse(processedHorse);
          setError(null);
        } else {
          // ローカルAPIルートを使用（開発環境用）
          console.log(`[HorseDetail] PROD_API_BASE_URL not set, using local API`);
          const response = await fetch(`/api/horses/${params.id}`, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
              'Content-Type': 'application/json',
            },
            redirect: 'follow'
          });

          if (!response.ok) {
            throw new Error('データの取得に失敗しました');
          }

          const horseData = await response.json();

          if (!horseData) {
            throw new Error('データが空です');
          }

          // 馬の基本情報を整形
          const processedHorse: Horse = {
            ...horseData,
            // 基本情報をトップレベルに展開
            name: horseData.name || '',
            sex: horseData.sex || '',
            age: horseData.age || 0,
            sire: horseData.sire || '',
            dam: horseData.dam || '',
            damsire: horseData.damsire || '',
            // メタデータ
            metadata: {
              created_at: horseData.metadata?.created_at || new Date().toISOString(),
              updated_at: horseData.metadata?.updated_at || new Date().toISOString(),
              data_source: horseData.metadata?.data_source || 'jbis'
            },
            // レコード情報
            race_record: horseData.race_record || {
              total_races: 0,
              wins: 0,
              total_prize_money: 0
            },
            // オークション情報
            latest_auction: horseData.latest_auction || null,
            auction_history: horseData.auction_history || []
          };

          setHorse(processedHorse);
          setError(null);
        }
      } catch (err) {
        console.error('馬データの取得中にエラーが発生しました:', err);
        setError('馬データの取得中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !horse) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-red-700">
                {error || '馬の情報を取得できませんでした'}
              </p>
            </div>
          </div>
        </div>
        <div className="mt-4">
          <Button
            onClick={() => router.back()}
            variant="outline"
          >
            一覧に戻る
          </Button>
        </div>
      </div>
    );
  }


  return <HorseDetailContent horse={horse} auctionHistory={horse.latest_auction || null} />;
};

const HorseDetailContent = ({ horse, auctionHistory }: HorseDetailContentProps) => {
  const router = useRouter();

  // オークション情報を取得（互換性のため）
  const auctionInfo = horse.latest_auction || auctionHistory;

  // 基本情報を取得
  const basicInfo = horse.basic_info || {
    name: horse.name || '',
    sex: '牡',
    age: 0,
    sire: '',
    dam: '',
    damsire: '',
    color: '',
    birthday: '',
    image_url: '',
    jbis_url: '',
    auction_url: '',
    is_retired: false,
    retirement_date: '',
    disease_tags: [],
    comment: ''
  };

  // 最新オークション情報を取得
  const latestAuction = horse.latest_auction;

  // 血統情報を抽出
  const sire = basicInfo.sire || '';
  const dam = basicInfo.dam || '';
  const damsire = basicInfo.damsire || '';
  const color = basicInfo.color || '';
  const birthday = basicInfo.birthday || '';
  const imageUrl = basicInfo.image_url || '';
  const jbisUrl = basicInfo.jbis_url || '';
  const auctionUrl = basicInfo.auction_url || '';

  // 疾病タグと健康状態
  const diseaseTags = horse.disease_tags || [];
  const healthIssues: string[] = [];

  // コメントを取得（互換性のため）
  const comment = auctionInfo?.comment;

  return (
    <div>
      <Header pageTitle={`${horse.name} の詳細`} />

      <div className="container mx-auto px-4 py-6">

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* メインコンテンツ */}
          <div className="lg:col-span-2 space-y-6">
            {/* 基本情報カード */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <h1 className="text-2xl font-bold">{horse.name}</h1>
                    <div className="flex items-center space-x-2">
                      {horse.sex && <span className="text-gray-600">{horse.sex}</span>}
                      {horse.age && (
                        <span className="text-gray-600">{horse.age}歳</span>
                      )}
                    </div>
                  </div>
                  {horse.disease_tags && (
                    <div className="flex flex-wrap justify-end gap-1">
                      {Array.isArray(horse.disease_tags)
                        ? horse.disease_tags.map((tag, index) => (
                          <Badge key={index} variant="secondary" className="bg-red-100 text-red-800 text-xs">
                            {tag.trim()}
                          </Badge>
                        ))
                        : String(horse.disease_tags).split(',').map((tag, index) => (
                          <Badge key={index} variant="secondary" className="bg-red-100 text-red-800 text-xs">
                            {tag.trim()}
                          </Badge>
                        ))
                      }
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* 馬画像 - カードいっぱいに表示 */}
                  <div className="w-full">
                    <div className="relative aspect-[4/3] w-full overflow-hidden rounded-lg bg-gray-100">
                      {imageUrl ? (
                        <Image
                          src={imageUrl}
                          alt={horse.name}
                          fill
                          className="object-cover"
                          sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                          priority
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center bg-gray-50 text-gray-400">
                          画像なし
                        </div>
                      )}
                    </div>
                  </div>

                  {/* レース戦績と血統情報 - 横並び表示 */}
                  <div className="space-y-4">
                    {/* レース戦績 */}
                    {horse.race_records && (
                      <div className="flex items-center gap-2 text-sm text-gray-600">
                        <span className="text-gray-600 font-medium whitespace-nowrap">獲得賞金：</span>
                        <span>{formatPrize(horse.race_records.total_prize_money, horse.race_records)}</span>
                        {horse.race_records.last_race_date && (
                          <span className="ml-2 text-xs text-gray-500">
                            (最終出走: {formatDate(horse.race_records.last_race_date)})
                          </span>
                        )}
                      </div>
                    )}

                    {/* 血統情報 - 横並び表示 */}
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      {latestAuction?.comment && (
                        <div className="mt-4 p-4 bg-yellow-50 border-l-4 border-yellow-400">
                          <p className="text-yellow-700">{latestAuction.comment}</p>
                        </div>
                      )}
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">父：</span>
                          <span>{sire || '不明'}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">母：</span>
                          <span>{dam || '不明'}</span>
                        </div>
                      </div>
                      <div>
                        <div className="flex items-baseline gap-1">
                          <span className="text-gray-600">母父：</span>
                          <span>{damsire || '不明'}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 毛色と生年月日 */}
                  <div className="flex flex-wrap gap-2 text-sm text-gray-600">
                    {basicInfo.color && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600 font-medium">毛色：</span>
                        <span>{basicInfo.color}</span>
                      </div>
                    )}
                    {basicInfo.birthday && (
                      <div className="flex items-center gap-1">
                        <span className="text-gray-600 font-medium">生年月日：</span>
                        <span>{formatDate(basicInfo.birthday)}</span>
                      </div>
                    )}
                  </div>

                  {/* 外部リンクボタン */}
                  <div className="flex gap-2 mt-2">
                    {basicInfo.jbis_url && (
                      <a
                        href={basicInfo.jbis_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <ExternalLink className="w-4 h-4" />
                        JBIS
                      </a>
                    )}
                    {basicInfo.auction_url && (
                      <a
                        href={basicInfo.auction_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
                      >
                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                        </svg>
                        サラブレッドオークション
                      </a>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* サイドバー - 価格・賞金情報 */}
          <div className="lg:col-span-1 space-y-6">
            {/* 落札価格情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">落札価格</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center">
                  <div className="text-2xl font-bold text-red-600">
                    {displayPrice(horse, auctionHistory)}
                  </div>
                  {auctionHistory?.price && (
                    <div className="mt-2 text-sm text-gray-600">
                      {formatPrize(horse.race_records?.total_prize_money || 0, horse.race_records)}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* 馬体重情報 */}
            {latestAuction?.weight && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">馬体重</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">
                    {latestAuction.weight} kg
                  </div>
                  {latestAuction.date && (
                    <div className="text-sm text-gray-600 mt-1">
                      計測日: {formatDate(latestAuction.date)}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* 戦績情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">戦績</CardTitle>
              </CardHeader>
              <CardContent>
                {horse.race_records ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500">獲得賞金</p>
                        <p className="font-medium">
                          {horse.race_records?.total_races === 0 ?
                            '未出走' :
                            formatPrize(horse.race_records?.total_prize_money, horse.race_records)}
                        </p>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500">最終出走日</p>
                        <p className="font-medium">
                          {horse.race_records.last_race_date ?
                            formatDate(horse.race_records.last_race_date) : '未出走'}
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500">戦績情報はありません</p>
                )}
              </CardContent>
            </Card>


            {/* オークション情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">オークション情報</CardTitle>
              </CardHeader>
              <CardContent>
                {auctionInfo ? (
                  <div className="space-y-4">
                    {/* コメント表示 */}
                    {latestAuction?.comment && (
                      <div className="mb-4 p-3 bg-yellow-50 border-l-4 border-yellow-400 rounded">
                        <h4 className="font-medium text-yellow-700 mb-1">コメント</h4>
                        <p className="text-yellow-800 text-sm whitespace-pre-wrap">{latestAuction.comment}</p>
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-gray-500">開催日</div>
                        <div className="font-medium">{formatDate(auctionInfo.date)}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">落札価格</div>
                        <div className="font-medium">
                          {auctionInfo.is_unsold
                            ? '主取り'
                            : auctionInfo.price
                              ? `${(auctionInfo.price / 10000).toLocaleString()}万円`
                              : '不明'}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <div className="text-sm text-gray-500">売主</div>
                        <div className="font-medium">{auctionInfo.seller || '不明'}</div>
                      </div>
                      <div>
                        <div className="text-sm text-gray-500">馬体重</div>
                        <div className="font-medium">
                          {auctionInfo.weight ? `${auctionInfo.weight}kg` : '計測なし'}
                        </div>
                      </div>
                    </div>

                    {comment && (
                      <div className="mt-2">
                        <div className="text-sm text-gray-500 mb-1">コメント</div>
                        <div className="text-sm whitespace-pre-line bg-gray-50 p-3 rounded">
                          {comment}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    オークション情報がありません
                  </div>
                )}
              </CardContent>
            </Card>

            {/* 賞金情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">賞金情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* メタ情報 */}
                  <div className="space-y-2 text-sm text-gray-600">
                    <div className="font-medium">登録情報</div>
                    <div>登録日: {formatDate(horse.metadata?.created_at) || '不明'}</div>
                    {horse.metadata?.updated_at && (
                      <div>更新日: {formatDate(horse.metadata.updated_at)}</div>
                    )}
                    <div>ID: {horse.id}</div>
                  </div>

                  {/* 賞金情報 */}
                  {horse.race_records?.total_prize_money !== undefined && (
                    <div className="space-y-2">
                      <div className="font-medium text-sm text-gray-600">レース成績</div>
                      <div className="flex items-center gap-2 text-sm">
                        <span className="text-gray-600">獲得賞金：</span>
                        <span className="font-medium">
                          {formatPrize(horse.race_records.total_prize_money, horse.race_records)}
                        </span>
                      </div>
                      {horse.race_records.last_race_date && (
                        <div className="text-sm">
                          <span className="text-gray-600">最終出走：</span>
                          <span>{formatDate(horse.race_records.last_race_date)}</span>
                        </div>
                      )}
                      {horse.race_records.last_prize_update && (
                        <div className="text-xs text-gray-500 mt-1">
                          賞金更新: {formatDate(horse.race_records.last_prize_update)}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* データ更新日 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">データ情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {auctionHistory?.auction_date && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">オークション日:</span>
                    <span>{formatDate(auctionHistory.auction_date)}</span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-600">作成日:</span>
                  <span>{horse.metadata?.created_at ? formatDate(horse.metadata.created_at) : '-'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">更新日:</span>
                  <span>{horse.metadata?.updated_at ? formatDate(horse.metadata.updated_at) : '-'}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* コメント */}
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">コメント</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-gray-700 whitespace-pre-line">
                {latestAuction?.comment || 'コメントはありません'}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HorseDetailPage;
