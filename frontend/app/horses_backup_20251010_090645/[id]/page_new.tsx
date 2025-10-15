'use client';

import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { Button } from '@mui/material/Button';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Typography from '@mui/material/Typography';
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import Box from '@mui/material/Box';
import Badge from '@mui/material/Badge';
import HorseImage from '@/components/HorseImage';

// --- 型定義 ---
interface HorseHistory {
  auction_date: string;
{{ ... }}
  name: string;
  sex: string;
  age: string;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number | null;
  total_prize_start: number;
  unsold?: boolean;
  detail_url?: string;
  primary_image?: string;
  disease_tags?: string;
  weight?: number;
  created_at: string;
  updated_at: string;
}

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: string;
  color: string;
  birthday: string;
  history: HorseHistory[];
  sire: string;
  dam: string;
  dam_sire: string;
  primary_image: string;
  disease_tags: string;
  jbis_url: string;
  weight: number | null;
  unsold_count: number | null;
  total_prize_latest: number;
  created_at: string;
  updated_at: string;
  unsold?: boolean;
  sold_price?: number | null;
  detail_url?: string;
  race_record?: string;
}

interface HorseData {
  metadata: any;
  horses: Horse[];
}

interface CommentedHistory extends HorseHistory {
  originalIndex: number;
}

interface HorseDetailContentProps {
  horse: Horse;
}

type AvailableHorse = {
  id: string;
  name: string;
};

// 日付フォーマット用のヘルパー関数
function formatDate(dateString: string | null | undefined) {
  if (!dateString) return '不明';
  try {
    const date = new Date(dateString);
    // 無効な日付の場合はエラーをスロー
    if (isNaN(date.getTime())) {
      throw new Error('無効な日付です');
    }
    return format(date, 'yyyy/MM/dd', { locale: ja });
  } catch (e) {
    console.error(`日付のフォーマットに失敗しました: ${dateString}`, e);
    return '不明';
  }
}

const toArray = (val: any) => (Array.isArray(val) ? val : val ? [val] : []);
const formatManYen = (val: number | null | undefined) => val ? `${(val / 10000).toFixed(1)}万` : '-';

// 画像のURLを取得するヘルパー関数
function getImageUrl(imagePath: string | undefined | null) {
  if (!imagePath) return null;
  // すでにフルURLの場合はそのまま返す
  if (imagePath.startsWith('http')) return imagePath;
  // 相対パスの場合はそのまま返す（Next.jsのImageコンポーネントはpublicフォルダを自動で解決）
  return imagePath.startsWith('/') ? imagePath : `/images/${imagePath}`;
}

// 落札価格表示用関数
function displayPrice(price: number | null | undefined, unsold: boolean | undefined) {
  if (unsold) return '主取り';
  if (!price && price !== 0) return '-';
  return `${price.toLocaleString()}円`;
}

// 成長率計算
function calculateGrowthRate(start: number, latest: number) {
  if (start === 0) return 0;
  return ((latest - start) / start) * 100;
}

// 賞金表示用関数
function formatPrize(val: number | string | null | undefined) {
  if (val === null || val === undefined) return '-';
  if (typeof val === 'string') return val;
  return `${val.toLocaleString()}万円`;
}

// エラーコンポーネント
function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="p-4 bg-red-50 rounded-md">
      <div className="flex">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clipRule="evenodd"
            />
          </svg>
        </div>
        <div className="ml-3">
          <p className="text-sm font-medium text-red-800">{message}</p>
          {onRetry && (
            <div className="mt-2">
              <button
                type="button"
                onClick={onRetry}
                className="bg-white rounded-md text-sm font-medium text-red-800 hover:text-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              >
                再試行
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ローディングコンポーネント
function LoadingSpinner() {
  return (
    <div className="flex justify-center items-center p-8">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      <span className="ml-2">読み込み中...</span>
    </div>
  );
}

// シンプルなエラーコンポーネント
const SimpleError: React.FC<{ 
  message: string;
  availableHorses?: Array<{id: string, name: string}>;
  onSelectHorse?: (id: string) => void;
}> = ({ 
  message, 
  availableHorses = [],
  onSelectHorse 
}) => {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        <h2 className="text-xl font-bold text-red-600 mb-4">エラーが発生しました</h2>
        <p className="mb-6">{message}</p>
        
        {availableHorses.length > 0 && (
          <div className="mb-6">
            <p className="font-medium mb-2">利用可能な馬:</p>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {availableHorses.map((horse) => (
                <div 
                  key={horse.id} 
                  onClick={() => onSelectHorse?.(horse.id)}
                  className="p-2 hover:bg-gray-100 rounded cursor-pointer"
                >
                  <div className="font-medium">{horse.name}</div>
                  <div className="text-sm text-gray-500">ID: {horse.id}</div>
                </div>
              ))}
            </div>
          </div>
        )}
        
        <button
          onClick={() => window.location.reload()}
          className="w-full bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 transition-colors"
        >
          再読み込み
        </button>
      </div>
    </div>
  );
};

// シンプルなローディングコンポーネント
const SimpleLoading = () => (
  <div className="min-h-screen flex items-center justify-center">
    <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
  </div>
);

// ページコンポーネントのプロパティ型
type PageProps = {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
};

// 馬詳細ページコンポーネント
export default function HorseDetailPage({ params }: PageProps) {
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [availableHorses, setAvailableHorses] = useState<AvailableHorse[]>([]);

  const fetchHorseData = useCallback(async (horseId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/horses/${horseId}`);
      const data = await response.json();
      
      if (!response.ok) {
        // バックエンドから利用可能な馬のリストが返されている場合
        if (data.detail?.available_horses) {
          setAvailableHorses(data.detail.available_horses);
        } else {
          // 利用可能な馬のリストがなければ、全馬を取得して表示
          try {
            const availableResponse = await fetch('/api/horses?limit=10');
            if (availableResponse.ok) {
              const horsesData = await availableResponse.json();
              setAvailableHorses(horsesData.horses || []);
            }
          } catch (e) {
            console.error('利用可能な馬の取得に失敗しました:', e);
          }
        }
        
        throw new Error(data.detail?.error || '指定された馬が見つかりませんでした');
      }

      setHorse(data);
    } catch (err) {
      console.error('馬データの取得中にエラーが発生しました:', err);
      setError(err instanceof Error ? err.message : '不明なエラーが発生しました');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (params.id) {
      fetchHorseData(params.id);
    }
  }, [params.id, fetchHorseData]);

  const handleSelectHorse = (id: string) => {
    router.push(`/horses/${id}`);
  };

  if (loading) {
    return <SimpleLoading />;
  }

  if (error || !horse) {
    return (
      <SimpleError 
        message={error || '馬の情報を取得できませんでした'} 
        availableHorses={availableHorses}
        onSelectHorse={(id) => router.push(`/horses/${id}`)}
      />
    );
  }

  return <HorseDetailContent horse={horse} />;
}

// 馬詳細コンテンツコンポーネント
function HorseDetailContent({ horse }: HorseDetailContentProps) {
  const [tabValue, setTabValue] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  // 最新のオークション履歴を取得
  const latestAuction = useMemo(() => {
    if (!horse.history || horse.history.length === 0) return null;
    return [...horse.history].sort((a, b) => 
      new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime()
    )[0];
  }, [horse.history]);

  // コメント付きの履歴を生成
  const commentedHistory = useMemo(() => {
    if (!horse.history) return [];
    
    return horse.history.map((record, index) => ({
      ...record,
      originalIndex: index,
    }));
  }, [horse.history]);

  // タブの状態管理
  const [activeTab, setActiveTab] = useState('info');

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <Button variant="outline" asChild>
          <Link href="/horses">
            ← 馬一覧に戻る
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左カラム */}
        <div className="lg:col-span-1">
          <Card className="mb-6">
            <CardHeader>
              <div className="flex justify-between items-start">
                <div>
                  <CardTitle className="text-2xl font-bold">{horse.name}</CardTitle>
                  <CardDescription className="mt-1">
                    {horse.sex} {horse.age}歳
                  </CardDescription>
                </div>
                {horse.unsold && (
                  <Badge variant="destructive" className="ml-2">
                    主取り
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              <div className="relative w-full aspect-square">
                {getImageUrl(horse.primary_image) ? (
                  <Image
                    src={getImageUrl(horse.primary_image) as string}
                    alt={horse.name}
                    fill
                    className="object-cover rounded-lg shadow-md"
                    priority
                  />
                ) : (
                  <div className="w-full h-full bg-gray-200 rounded-lg flex items-center justify-center">
                    <span className="text-gray-500">No Image</span>
                  </div>
                )}
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-500">血統</h3>
                  <div className="mt-1 space-y-1">
                    <p>父: {horse.sire || '不明'}</p>
                    <p>母: {horse.dam || '不明'}</p>
                    <p>母の父: {horse.dam_sire || '不明'}</p>
                  </div>
                </div>

                {horse.weight && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">馬体重</h3>
                    <p>{horse.weight}kg</p>
                  </div>
                )}

                {horse.disease_tags && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">病歴</h3>
                    <div className="flex flex-wrap gap-2 mt-1">
                      {horse.disease_tags.split(',').map((tag) => (
                        <Badge key={tag} variant="outline">
                          {tag.trim()}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {latestAuction && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">最新のオークション情報</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div>
                    <span className="text-sm text-gray-500">日付: </span>
                    <span>{formatDate(latestAuction.auction_date)}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">落札価格: </span>
                    <span>{displayPrice(latestAuction.sold_price, latestAuction.unsold)}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">売主: </span>
                    <span>{latestAuction.seller || '不明'}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">オークション時賞金: </span>
                    <span>{formatPrize(latestAuction.total_prize_start)}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">現在の賞金: </span>
                    <span>{formatPrize(horse.total_prize_latest)}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 右カラム */}
        <div className="lg:col-span-2">
          <Card>
            <Tabs 
              defaultValue="info" 
              value={activeTab}
              onValueChange={setActiveTab}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="info">基本情報</TabsTrigger>
                <TabsTrigger value="history">オークション履歴</TabsTrigger>
                <TabsTrigger value="comments">コメント</TabsTrigger>
              </TabsList>

              <TabsContent value="info" className="p-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">生年月日</h3>
                    <p>{formatDate(horse.birthday)}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">毛色</h3>
                    <p>{horse.color || '不明'}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-gray-500">JBIS</h3>
                    {horse.jbis_url ? (
                      <a 
                        href={horse.jbis_url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline"
                      >
                        JBISページを開く
                      </a>
                    ) : (
                      <p>情報なし</p>
                    )}
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="history" className="p-6">
                {horse.history && horse.history.length > 0 ? (
                  <div className="space-y-4">
                    {[...horse.history]
                      .sort((a, b) => new Date(b.auction_date).getTime() - new Date(a.auction_date).getTime())
                      .map((record, index) => (
                        <Card key={index} className="p-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-medium">{formatDate(record.auction_date)}</h4>
                              <p className="text-sm text-gray-500">
                                {record.seller && `売主: ${record.seller}`}
                              </p>
                            </div>
                            <div className="text-right">
                              <p className="font-medium">
                                {displayPrice(record.sold_price, record.unsold)}
                              </p>
                              <p className="text-sm text-gray-500">
                                賞金: {formatPrize(record.total_prize_start)}
                              </p>
                            </div>
                            {record.comment && (
                              <div className="col-span-2 mt-2 pt-2 border-t border-gray-100">
                                <p className="text-sm text-gray-700 whitespace-pre-line">
                                  {record.comment}
                                </p>
                              </div>
                            )}
                          </div>
                        </Card>
                      ))}
                  </div>
                ) : (
                  <p className="text-gray-500">オークション履歴がありません</p>
                )}
              </TabsContent>

              <TabsContent value="comments" className="p-6">
                {commentedHistory.length > 0 ? (
                  <div className="space-y-4">
                    {commentedHistory
                      .filter(record => record.comment)
                      .map((record, index) => (
                        <Card key={index} className="p-4">
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="font-medium">{formatDate(record.auction_date)}</h4>
                              {record.seller && (
                                <p className="text-sm text-gray-500">
                                  売主: {record.seller}
                                </p>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="font-medium">
                                {displayPrice(record.sold_price, record.unsold)}
                              </p>
                            </div>
                          </div>
                          <div className="mt-3 pt-3 border-t border-gray-100">
                            <p className="whitespace-pre-line">
                              {record.comment}
                            </p>
                          </div>
                        </Card>
                      ))}
                  </div>
                ) : (
                  <p className="text-gray-500">コメントがありません</p>
                )}
              </TabsContent>
            </Tabs>
          </Card>
        </div>
      </div>
    </div>
  );
}
