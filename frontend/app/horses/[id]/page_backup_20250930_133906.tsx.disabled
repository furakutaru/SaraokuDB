'use client';

import { useState, useEffect, useMemo, useCallback, ReactNode } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import Button from '@mui/material/Button';
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
  [key: string]: any; // 追加のプロパティに対応
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
  [key: string]: any; // 追加のプロパティに対応
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

interface AvailableHorse {
  id: string;
  name: string;
}

// 日付フォーマット用のヘルパー関数
function formatDate(dateString: string): string {
  if (!dateString) return '不明';
  try {
    const date = new Date(dateString);
    if (isNaN(date.getTime())) {
      throw new Error('無効な日付です');
    }
    return format(date, 'yyyy/MM/dd', { locale: ja });
  } catch (e) {
    console.error(`日付のフォーマットに失敗しました: ${dateString}`, e);
    return '不明';
  }
}

// 配列に変換するユーティリティ関数
const toArray = (val: any) => (Array.isArray(val) ? val : val ? [val] : []);

// 万円表示に変換するユーティリティ関数
const formatManYen = (val: number | null | undefined): string => 
  val ? `${(val / 10000).toFixed(1)}万` : '-';

// 落札価格表示用関数
function displayPrice(price: number | null | undefined, unsold: boolean | undefined): string {
  if (unsold) return '主取り';
  if (price === null || price === undefined) return '-';
  return `${price.toLocaleString()}円`;
}

// 成長率計算
function calculateGrowthRate(start: number, latest: number): number {
  if (start === 0) return 0;
  return ((latest - start) / start) * 100;
}

// 賞金表示用関数
function formatPrize(val: number | string | null | undefined): string {
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
        onSelectHorse={handleSelectHorse}
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
        <Button 
          variant="outlined" 
          startIcon={<span>←</span>} 
          component={Link} 
          href="/horses"
        >
          馬一覧に戻る
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 左カラム */}
        <div className="lg:col-span-1">
          <Card className="mb-6">
            <CardHeader
              title={
                <Box display="flex" alignItems="center" justifyContent="space-between">
                  <Typography variant="h5" component="div">
                    {horse.name}
                  </Typography>
                  {horse.unsold && (
                    <Badge color="error" badgeContent="主取り" />
                  )}
                </Box>
              }
              subheader={`${horse.sex} ${horse.age}歳`}
            />
            <CardContent>
              <Box sx={{ position: 'relative', width: '100%', aspectRatio: '1/1', mb: 3 }}>
                {horse.primary_image ? (
                  <Image
                    src={horse.primary_image}
                    alt={horse.name}
                    fill
                    style={{ objectFit: 'cover', borderRadius: '8px' }}
                    priority
                  />
                ) : (
                  <Box 
                    sx={{ 
                      width: '100%', 
                      height: '100%', 
                      bgcolor: 'grey.200', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center',
                      borderRadius: 1
                    }}
                  >
                    <Typography color="text.secondary">No Image</Typography>
                  </Box>
                )}
              </Box>
              
              <Box sx={{ '& > *:not(:last-child)': { mb: 2 } }}>
                <div>
                  <Typography variant="subtitle2" color="text.secondary">血統</Typography>
                  <Box sx={{ pl: 1, mt: 0.5 }}>
                    <Typography>父: {horse.sire || '不明'}</Typography>
                    <Typography>母: {horse.dam || '不明'}</Typography>
                    <Typography>母の父: {horse.dam_sire || '不明'}</Typography>
                  </Box>
                </div>

                {horse.weight && (
                  <div>
                    <Typography variant="subtitle2" color="text.secondary">馬体重</Typography>
                    <Typography>{horse.weight}kg</Typography>
                  </div>
                )}

                {horse.disease_tags && (
                  <div>
                    <Typography variant="subtitle2" color="text.secondary">病歴</Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 0.5 }}>
                      {horse.disease_tags.split(',').map((tag: string, index: number) => (
                        <Badge 
                          key={index} 
                          variant="outlined" 
                          sx={{ 
                            borderColor: 'divider',
                            color: 'text.secondary',
                            px: 1,
                            py: 0.5,
                            borderRadius: 1
                          }}
                        >
                          {tag.trim()}
                        </Badge>
                      ))}
                    </Box>
                  </div>
                )}
              </Box>
            </CardContent>
          </Card>

          {latestAuction && (
            <Card>
              <CardHeader
                title={
                  <Typography variant="h6">最新のオークション情報</Typography>
                }
              />
              <CardContent>
                <Box sx={{ '& > *:not(:last-child)': { mb: 1 } }}>
                  <div>
                    <Typography variant="body2" color="text.secondary">日付:</Typography>
                    <Typography>{formatDate(latestAuction.auction_date)}</Typography>
                  </div>
                  <div>
                    <Typography variant="body2" color="text.secondary">落札価格:</Typography>
                    <Typography>{displayPrice(latestAuction.sold_price, latestAuction.unsold)}</Typography>
                  </div>
                  {latestAuction.seller && (
                    <div>
                      <Typography variant="body2" color="text.secondary">売主:</Typography>
                      <Typography>{latestAuction.seller}</Typography>
                    </div>
                  )}
                  {latestAuction.comment && (
                    <div>
                      <Typography variant="body2" color="text.secondary">コメント:</Typography>
                      <Typography>{latestAuction.comment}</Typography>
                    </div>
                  )}
                </Box>
              </CardContent>
            </Card>
          )}
        </div>

        {/* 右カラム */}
        <div className="lg:col-span-2">
          <Card>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ borderBottom: 1, borderColor: 'divider' }}
            >
              <Tab label="基本情報" />
              <Tab label="オークション履歴" />
              <Tab label="血統情報" />
            </Tabs>

            <CardContent>
              {tabValue === 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>基本情報</Typography>
                  <Box sx={{ '& > *:not(:last-child)': { mb: 2 } }}>
                    <div>
                      <Typography variant="subtitle2" color="text.secondary">馬名</Typography>
                      <Typography>{horse.name}</Typography>
                    </div>
                    <div>
                      <Typography variant="subtitle2" color="text.secondary">性別・年齢</Typography>
                      <Typography>{horse.sex} {horse.age}歳</Typography>
                    </div>
                    {horse.birthday && (
                      <div>
                        <Typography variant="subtitle2" color="text.secondary">生年月日</Typography>
                        <Typography>{formatDate(horse.birthday)}</Typography>
                      </div>
                    )}
                    {horse.color && (
                      <div>
                        <Typography variant="subtitle2" color="text.secondary">毛色</Typography>
                        <Typography>{horse.color}</Typography>
                      </div>
                    )}
                    {horse.jbis_url && (
                      <div>
                        <Typography variant="subtitle2" color="text.secondary">JBIS</Typography>
                        <Link href={horse.jbis_url} target="_blank" rel="noopener noreferrer">
                          <Button 
                            variant="outlined" 
                            size="small"
                            startIcon={<span>🔗</span>}
                          >
                            JBISで確認
                          </Button>
                        </Link>
                      </div>
                    )}
                  </Box>
                </Box>
              )}

              {tabValue === 1 && (
                <Box>
                  <Typography variant="h6" gutterBottom>オークション履歴</Typography>
                  {commentedHistory.length > 0 ? (
                    <Box sx={{ overflowX: 'auto' }}>
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">日付</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">落札価格</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">売主</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">コメント</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {commentedHistory.map((record, index) => (
                            <tr key={index}>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatDate(record.auction_date)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                {displayPrice(record.sold_price, record.unsold)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {record.seller || '-'}
                              </td>
                              <td className="px-6 py-4 text-sm text-gray-500">
                                {record.comment || '-'}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </Box>
                  ) : (
                    <Typography>オークション履歴はありません</Typography>
                  )}
                </Box>
              )}

              {tabValue === 2 && (
                <Box>
                  <Typography variant="h6" gutterBottom>血統情報</Typography>
                  <Box sx={{ '& > *:not(:last-child)': { mb: 2 } }}>
                    <div>
                      <Typography variant="subtitle2" color="text.secondary">父</Typography>
                      <Typography>{horse.sire || '不明'}</Typography>
                    </div>
                    <div>
                      <Typography variant="subtitle2" color="text.secondary">母</Typography>
                      <Typography>{horse.dam || '不明'}</Typography>
                    </div>
                    <div>
                      <Typography variant="subtitle2" color="text.secondary">母の父</Typography>
                      <Typography>{horse.dam_sire || '不明'}</Typography>
                    </div>
                    {horse.dam && horse.dam_sire && (
                      <div>
                        <Typography variant="subtitle2" color="text.secondary">母系</Typography>
                        <Typography>{horse.dam} - {horse.dam_sire}</Typography>
                      </div>
                    )}
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
