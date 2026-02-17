'use client';

import { useState, useEffect } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { format, parseISO } from 'date-fns';
import { ja } from 'date-fns/locale';
import { ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { formatPrize } from '@/utils/format';
import { getApiBase } from '@/lib/utils';
import Image from 'next/image';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
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
  // オークション履歴から価格を取得を最優先
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

  // 価格情報がなく、未出走の場合は「未出走」
  if (horse.race_records?.total_races === 0) {
    return '未出走';
  }

  // いずれも見つからない場合
  return '-';
};

// コメントを折り畳み表示するコンポーネント
const CollapsibleComment = ({ content }: { content: string }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLong = content.length > 150;

  if (!isLong) {
    return (
      <div className="whitespace-pre-line p-4 bg-gray-50 rounded-md border border-gray-200">
        {content}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className={`whitespace-pre-line p-4 bg-gray-50 rounded-md border border-gray-200 overflow-hidden transition-all duration-300 ${isExpanded ? 'max-h-[1000px]' : 'max-h-[120px] relative'}`}>
        {content}
        {!isExpanded && (
          <div className="absolute bottom-0 left-0 right-0 h-12 bg-gradient-to-t from-gray-50 to-transparent pointer-events-none" />
        )}
      </div>
      <Button
        variant="ghost"
        size="sm"
        className="w-full flex items-center justify-center gap-2 text-gray-500 hover:text-gray-700 h-8"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        {isExpanded ? (
          <>
            閉じる <ChevronUp className="w-4 h-4" />
          </>
        ) : (
          <>
            全文を表示 <ChevronDown className="w-4 h-4" />
          </>
        )}
      </Button>
    </div>
  );
};

// --- コンポーネント ---
const HorseDetailPage = () => {
  const router = useRouter();
  const params = useParams();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [horse, setHorse] = useState<Horse | null>(null);
  const [auctionHistory, setAuctionHistory] = useState<AuctionHistory | null>(null);


  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        setIsLoading(true);
        // getApiBase関数を使用してAPI URLを取得
        const API_BASE = getApiBase();
        const API_URL = `${API_BASE}/api`;

        // デバッグログ
        console.log(`[HorseDetail] API_BASE: ${API_BASE}`);
        console.log(`[HorseDetail] API_URL: ${API_URL}`);

        // バックエンドAPIからデータを取得
        const horseId = params.id as string;
        const backendUrl = `${API_URL}/horses/${horseId}`;
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
          race_records: horseData.race_records || {
            total_races: 0,
            wins: 0,
            total_prize_money: 0
          },
          // 互換性のための重複
          race_record: horseData.race_records || {
            total_races: 0,
            wins: 0,
            total_prize_money: 0
          },
          // オークション情報
          latest_auction: horseData.latest_auction || null,
          auction_history: horseData.auction_history || [],
        };

        setHorse(processedHorse);
        setError(null);
      } catch (error) {
        console.error('馬データの取得中にエラーが発生しました:', error);
        setError('馬データの取得中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id as string]);

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
  const [activeTab, setActiveTab] = useState<string>("0");

  // オークション情報を取得（互換性のため）
  const auctionInfo = horse.latest_auction || auctionHistory;

  // 基本情報を取得（APIデータはトップレベルに展開されている）
  const basicInfo = {
    name: horse.name || '',
    sex: horse.sex || '牡',
    age: horse.age || 0,
    sire: horse.sire || '',
    dam: horse.dam || '',
    damsire: horse.damsire || '',
    color: '', // APIにcolorフィールドがない
    birthday: '', // APIにbirthdayフィールドがない
    image_url: horse.image_url || '',
    jbis_url: horse.jbis_url || '',
    auction_url: horse.detail_url || '', // detail_urlを使用
    is_retired: horse.is_broodmare || false,
    retirement_date: '',
    disease_tags: horse.disease_tags || [],
    comment: horse.comment || ''
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

  // コメントを取得（トップレベルのcommentを使用）
  const comment = horse.comment || latestAuction?.comment;

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
                <div className="flex items-center space-x-4">
                  <h1 className="text-2xl font-bold">{horse.name}</h1>
                  <div className="flex items-center space-x-2">
                    {horse.sex && <span className="text-gray-600">{horse.sex}</span>}
                    {horse.age && (
                      <span className="text-gray-600">{horse.age}歳</span>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                {/* 2カラムレイアウト */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 左カラム: 画像 + リンク + 疾病情報 */}
                  <div className="space-y-4">
                    {/* 馬画像 */}
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

                    {/* 外部リンク */}
                    <div className="flex gap-2">
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
                          className="inline-flex items-center gap-1 text-sm text-blue-600 hover:underline"
                        >
                          <ExternalLink className="w-4 h-4" />
                          サラブレッドオークション
                        </a>
                      )}
                    </div>

                    {/* 疾病情報 */}
                    <div>
                      <div className="text-sm text-gray-600 mb-2">疾病情報</div>
                      {horse.disease_tags && (Array.isArray(horse.disease_tags) ? horse.disease_tags.length > 0 : String(horse.disease_tags).trim() !== '') ? (
                        <div className="flex flex-wrap gap-2">
                          {(Array.isArray(horse.disease_tags)
                            ? horse.disease_tags
                            : String(horse.disease_tags).split(',')
                          ).map((tag, index) => (
                            <span
                              key={index}
                              className="inline-block px-3 py-1 text-sm bg-white border border-gray-300 rounded-full"
                            >
                              {tag.trim()}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-gray-500 text-sm">なし</span>
                      )}
                    </div>
                  </div>

                  {/* 右カラム: 血統情報、レース戦績、売主、馬体重 */}
                  <div className="space-y-4">
                    {/* 血統情報 */}
                    <div>
                      <div className="text-sm text-gray-600 mb-2">血統情報</div>
                      <div className="space-y-1 text-sm">
                        <div>父: {sire || '不明'}</div>
                        <div>母: {dam || '不明'}</div>
                        <div>母父: {damsire || '不明'}</div>
                      </div>
                    </div>

                    {/* レース戦績、売主、馬体重 - 縦並び（各行内は横並び） */}
                    <div className="space-y-2 text-sm">
                      {/* レース戦績 */}
                      {horse.race_records && (
                        <div className="flex gap-2">
                          <span className="text-gray-600">レース戦績:</span>
                          <span>{horse.race_records.total_races || 0}戦{horse.race_records.wins || 0}勝</span>
                        </div>
                      )}

                      {/* 売主 */}
                      {horse.seller && (
                        <div className="flex gap-2">
                          <span className="text-gray-600">売主:</span>
                          <span>{horse.seller}</span>
                        </div>
                      )}

                      {/* 馬体重 */}
                      {(horse.weight || latestAuction?.weight) && (
                        <div className="flex gap-2">
                          <span className="text-gray-600">馬体重:</span>
                          <span>{horse.weight || latestAuction?.weight} kg</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* コメント */}
            {comment && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">コメント</CardTitle>
                </CardHeader>
                <CardContent>
                  <CollapsibleComment content={comment} />
                </CardContent>
              </Card>
            )}
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

            {/* 賞金情報 */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">賞金情報</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* 落札時賞金 */}
                {horse.total_prize_start !== undefined && horse.total_prize_start !== null && (
                  <div className="flex gap-2 items-baseline">
                    <span className="text-sm text-gray-600 w-12">落札時</span>
                    <span className="text-xl font-bold">{(horse.total_prize_start / 10000).toFixed(1)}万円</span>
                  </div>
                )}

                {/* 現在賞金 */}
                {(horse.total_prize_latest !== undefined && horse.total_prize_latest !== null) || horse.total_prize_start !== undefined ? (
                  <div className="flex gap-2 items-baseline">
                    <span className="text-sm text-gray-600 w-12">現在</span>
                    <span className="text-xl font-bold">
                      {(horse.total_prize_latest !== null && horse.total_prize_latest !== undefined)
                        ? `${(horse.total_prize_latest / 10000).toFixed(1)}万円`
                        : `${((horse.total_prize_start || 0) / 10000).toFixed(1)}万円`}
                    </span>
                  </div>
                ) : null}

                {/* 賞金増加額 */}
                {horse.total_prize_start !== undefined && (
                  <div className="p-3 bg-blue-50 rounded-md">
                    <div className="text-sm text-gray-600 mb-1">差分</div>
                    <div className="text-xl font-bold text-blue-700">
                      +{(Math.max(0, ((horse.total_prize_latest !== null && horse.total_prize_latest !== undefined) ? horse.total_prize_latest : horse.total_prize_start || 0) - (horse.total_prize_start || 0)) / 10000).toFixed(1)}万円
                    </div>
                    {horse.total_prize_start > 0 && (
                      <div className="text-xs text-gray-600 mt-1">
                        ({(((((horse.total_prize_latest !== null && horse.total_prize_latest !== undefined) ? horse.total_prize_latest : horse.total_prize_start || 0) - (horse.total_prize_start || 0)) / horse.total_prize_start) * 100).toFixed(1)}%)
                      </div>
                    )}
                  </div>
                )}
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

        {/* オークション履歴コメント（タブ表示） */}
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">オークションコメント</CardTitle>
            </CardHeader>
            <CardContent>
              {horse.auction_history && horse.auction_history.length > 0 ? (
                <Tabs value={activeTab} onValueChange={setActiveTab}>
                  {horse.auction_history.length > 1 && (
                    <TabsList className="mb-4">
                      {horse.auction_history.map((auction, index) => (
                        <TabsTrigger key={index} value={String(index)}>
                          {auction.auction_date ? formatDate(auction.auction_date) : `履歴 ${index + 1}`}
                        </TabsTrigger>
                      ))}
                    </TabsList>
                  )}
                  {horse.auction_history.map((auction, index) => (
                    <TabsContent key={index} value={String(index)}>
                      <div className="space-y-4">
                        {auction.comment ? (
                          <CollapsibleComment content={auction.comment} />
                        ) : (
                          <p className="text-gray-500">コメントはありません</p>
                        )}

                        {/* 馬体重情報 */}
                        {auction.weight && (
                          <div className="p-3 bg-blue-50 rounded-md border border-blue-100">
                            <div className="font-medium text-sm text-blue-900 mb-2">馬体重情報</div>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                              <div>馬体重: <span className="font-medium">{auction.weight} kg</span></div>
                              {auction.auction_date && (
                                <div>オークション日: <span className="font-medium">{formatDate(auction.auction_date)}</span></div>
                              )}
                            </div>
                          </div>
                        )}

                        {/* オークション詳細情報 */}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-600">売主:</span>
                            <span className="ml-2 font-medium">{auction.seller || '不明'}</span>
                          </div>
                          <div>
                            <span className="text-gray-600">落札価格:</span>
                            <span className="ml-2 font-medium">
                              {auction.is_unsold ? '主取り' : auction.price ? `${(auction.price / 10000).toLocaleString()}万円` : '-'}
                            </span>
                          </div>
                        </div>
                      </div>
                    </TabsContent>
                  ))}
                </Tabs>
              ) : (
                <p className="text-gray-500">オークション履歴がありません</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default HorseDetailPage;
