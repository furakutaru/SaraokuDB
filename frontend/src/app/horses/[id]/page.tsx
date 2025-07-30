'use client';

import { useState, useEffect, useMemo, useCallback } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/navigation';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { Button } from '@mui/material';
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
  sold_price: number;
  total_prize_start: number;
  unsold?: boolean;
  detail_url?: string; // サラオク公式ページへのリンク
  primary_image?: string; // 馬体画像のURL
  disease_tags?: string; // 病歴タグ
  weight?: number; // 体重
}

interface Horse {
  id: number;
  name: string; // 馬名
  sex: string; // 性別
  age: string; // 年齢
  color: string; // 毛色
  birthday: string; // 生年月日
  history: HorseHistory[];
  sire: string; // 父
  dam: string; // 母
  dam_sire: string; // 母の父
  primary_image: string; // メイン画像URL
  disease_tags: string; // 病歴タグ
  jbis_url: string; // JBIS URL
  weight: number | null; // 体重（またはnull）
  unsold_count: number | null; // 主取り回数
  total_prize_latest: number; // 最新賞金
  created_at: string;
  updated_at: string;
  unsold?: boolean;
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

interface PageProps {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

// 日付フォーマット用のヘルパー関数
const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'yyyy年M月d日', { locale: ja });
  } catch (e) {
    return dateString; // 日付が不正な場合はそのまま返す
  }
};

// --- 追加ユーティリティ ---
const toArray = (val: any) => Array.isArray(val) ? val : [val];
const formatManYen = (val: number) => isNaN(val) ? '-' : `${(val/10000).toFixed(1)}万円`;

// 落札価格表示用関数
// 落札価格は取得値そのまま（円単位）で表示すること。データは既に円単位で格納されている。
const displayPrice = (price: number | null | undefined, unsold: boolean | undefined) => {
  if (unsold === true) return '主取り';
  if (price === null || price === undefined) return '-';
  return '¥' + price.toLocaleString();
};

// 以前の仕様に合わせた成長率計算
const calculateGrowthRate = (start: number, latest: number) => {
  if (start === 0) return '-';
  const rate = ((latest - start) / start * 100).toFixed(1);
  return (latest - start >= 0 ? '+' : '') + rate;
};

// 賞金は万円単位で表示
// 現在の総賞金はJBISからスクレイピングして取得している点に注意。
const formatPrize = (val: number | string | null | undefined) => {
  if (val === null || val === undefined || val === '' || isNaN(Number(val))) return '-';
  return `${Number(val).toFixed(1)}万円`;
};

// エラーコンポーネント
function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
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

// ローディングコンポーネント
function LoadingSpinner() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary"></div>
    </div>
  );
}

/**
 * 馬データを取得する関数
 * @param horseId 取得する馬のID
 * @returns 馬データとエラー情報を含むオブジェクト
 */
async function getHorseData(horseId: number): Promise<{ horse: Horse | null; error: string | null }> {
  if (!horseId || isNaN(horseId) || horseId <= 0) {
    return { horse: null, error: '無効な馬IDです' };
  }

  try {
    // 静的ファイルからデータを取得
    const response = await fetch('/data/horses_history.json');
    
    if (!response.ok) {
      throw new Error(`データの取得に失敗しました (${response.status} ${response.statusText})`);
    }
    
    const data: HorseData = await response.json();
    
    // 指定されたIDの馬を検索
    const horse = data.horses.find(h => h.id === horseId);
    
    if (!horse) {
      throw new Error('指定された馬のデータが見つかりません');
    }
    
    return { horse, error: null };
  } catch (error) {
    console.error('馬データの取得中にエラーが発生しました:', error);
    return { 
      horse: null, 
      error: error instanceof Error ? error.message : '不明なエラーが発生しました' 
    };
  }
}

// シンプルなエラーコンポーネント
function SimpleError({ message }: { message: string }) {
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

// シンプルなローディングコンポーネント
function SimpleLoading() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );
}

// ページのパラメータ型
interface PageProps {
  params: { id: string };
  searchParams?: { [key: string]: string | string[] | undefined };
}

// ページコンポーネント (Client Component)
export default function HorseDetailPage({ params }: PageProps) {
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<number>(0);
  
  // 馬IDをパース (Next.js 14+ のparams Promise対応)
  const horseId = useMemo(() => {
    try {
      // params.id を直接使用（Next.jsが自動的に解決）
      const idParam = params?.id;
      
      // idが存在しないか無効な場合はエラー
      if (!idParam) {
        throw new Error('馬IDが指定されていません');
      }
      
      // 数値に変換
      const id = typeof idParam === 'string' ? parseInt(idParam, 10) : 0;
      
      if (isNaN(id) || id <= 0) {
        throw new Error('無効な馬IDです');
      }
      
      return id;
    } catch (e) {
      const errorMessage = e instanceof Error ? e.message : '無効な馬IDです';
      setError(errorMessage);
      setIsLoading(false);
      console.error('馬IDのパースに失敗しました:', errorMessage);
      return 0;
    }
  }, [params]);
  
  // コメントの有無をチェック
  const hasComments = useMemo(() => {
    if (!horse?.history) return false;
    return horse.history.some(history => 
      history.comment && history.comment.trim().length > 0
    );
  }, [horse]);
  
  // データ取得とエラー処理
  useEffect(() => {
    const fetchHorseData = async () => {
      if (!horseId) {
        setError('馬IDが指定されていません');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const { horse, error } = await getHorseData(horseId);
        
        if (error) {
          throw new Error(error);
        } 
        
        if (!horse) {
          throw new Error('馬のデータが見つかりませんでした');
        }

        // 必須フィールドのバリデーション
        if (!horse.name || !horse.primary_image || !horse.history?.length) {
          console.warn('不完全な馬データ:', horse);
        }

        setHorse(horse);
      } catch (err) {
        console.error('馬データの取得中にエラーが発生しました:', err);
        setError(err instanceof Error ? err.message : 'データの取得中にエラーが発生しました');
      } finally {
        setIsLoading(false);
      }
    };

    fetchHorseData();
  }, [horseId]);
  
  if (isLoading) {
    return <SimpleLoading />;
  }
  
  if (error) {
    return <SimpleError message={error} />;
  }
  
  if (!horse) {
    return <SimpleError message="馬のデータが見つかりませんでした" />;
  }
  
  // 馬詳細コンポーネントを表示
  return <HorseDetailContent horse={horse} />;
}

const HorseDetailContent = ({ horse }: HorseDetailContentProps) => {
  // タブの状態管理
  const [activeTab, setActiveTab] = useState(0);

  // タブ変更ハンドラー
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // コメントの有無をチェック
  const hasComments = useMemo(() => {
    return horse?.history?.some(h => h.comment?.trim()) || false;
  }, [horse?.history]);
  
  // コメントがある履歴のみをフィルタリング
  const tabsWithComments = useMemo<CommentedHistory[]>(() => {
    if (!horse?.history?.length) return [];
    return horse.history.reduce<CommentedHistory[]>((acc, history, index) => {
      if (history.comment?.trim()) {
        acc.push({ ...history, originalIndex: index });
      }
      return acc;
    }, []);
  }, [horse?.history]);
  
  // 初期表示時に最初のコメントがあるタブを選択
  useEffect(() => {
    if (tabsWithComments.length > 0) {
      setActiveTab(tabsWithComments[0].originalIndex);
    }
  }, [tabsWithComments]);
  
  // 馬のデータがない場合のエラー表示
  if (!horse) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-gray-500">馬のデータを読み込めませんでした</p>
          <Button component={Link} href="/" className="mt-4">
            トップに戻る
          </Button>
        </div>
      </div>
    );
  }

  // 最新の履歴をメモ化
  const latestHistory = useMemo(() => {
    if (!horse.history || horse.history.length === 0) return null;
    return horse.history[horse.history.length - 1];
  }, [horse.history]);

  // 性別の色とアイコンをメモ化
  const { sexColor, sexIcon } = useMemo(() => {
    // 馬の基本情報から性別を取得（履歴がなければデフォルトで空文字）
    const sex = horse.sex || latestHistory?.sex || '';
    let color = 'text-white';
    let bgColor = 'bg-gray-200';
    let icon = '';

    if (sex === '牡') {
      bgColor = 'bg-blue-600';
      icon = '♂';
    } else if (sex === '牝') {
      bgColor = 'bg-pink-500';
      icon = '♀';
    } else if (sex === 'セ' || sex === 'せん' || sex === 'セン') {
      bgColor = 'bg-green-600';
      color = 'text-white';
      icon = '⚥';
    }

    return { 
      sexColor: `text-white ${bgColor}`, // 常に白文字を強制
      sexIcon: icon 
    };
  }, [latestHistory?.sex]);

  if (!latestHistory) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1, color: 'text-gray-900' }}>データが見つかりません</Typography>
          <p className="text-gray-600 mb-6">この馬の情報を取得できませんでした。</p>
          <Link href="/horses">
            <Button>馬一覧に戻る</Button>
          </Link>
        </div>
      </div>
    );
  }

  // 落札価格フォーマット（円単位で保存されているので、そのまま表示）
  // const formatPrice = (price: number) => {
  //   return price.toLocaleString();
  // };

  // タグをレンダリングする関数
  const renderTags = (tags: string) => {
    if (!tags) return null;
    const tagList = tags.split(',').map(tag => tag.trim()).filter(Boolean);
    
    return (
      <div className="flex flex-wrap gap-2 mt-2">
        {tagList.map((tag, index) => (
          <span key={index} className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">
            {tag}
          </span>
        ))}
      </div>
    );
  };

  // 以前の仕様に合わせた成長率計算
  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <button
              onClick={() => window.history.back()}
              className="rounded-md bg-white border border-black text-black px-4 py-2 hover:bg-gray-100 transition-colors"
            >
              <svg className="w-5 h-5 mr-2 inline-block" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              戻る
            </button>
            <div className="flex gap-4">
              <Button 
                component={Link} 
                href="/" 
                variant="outlined" 
                className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
              >
                解析
              </Button>
              <Button 
                component={Link} 
                href="/horses" 
                variant="outlined" 
                className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
              >
                直近の追加
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* メイン情報 */}
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1 }}>{latestHistory.name}</Typography>
                    {/* 性別・年齢 */}
                    <div className="flex items-center gap-2">
                      <Badge className={sexColor}>
                        {horse.sex || latestHistory?.sex} {latestHistory?.age}歳
                      </Badge>
                    </div>
                  </div>
                  {/* JBISリンク */}
                  {horse.jbis_url && (
                    <a
                      href={horse.jbis_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                      <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                      JBIS
                    </a>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* 画像は最新履歴から取得 */}
                  <div className="flex justify-center w-full h-64">
                    {latestHistory.primary_image ? (
                      <HorseImage
                        src={latestHistory.primary_image}
                        alt={`${latestHistory.name}の画像`}
                        className="w-full h-full max-w-xs"
                      />
                    ) : (
                      <div className="w-full max-w-xs h-64 bg-gray-200 rounded-lg flex items-center justify-center">
                        <div className="text-center text-gray-500">
                          <svg className="w-16 h-16 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          <p>画像なし</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* 基本情報 */}
                  <div className="space-y-4">
                    <div>
                      <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>基本情報</Typography>
                      <div className="space-y-2 text-sm">
                        {/* 体重履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">体重:</span>
                          <span className="font-medium">{horse.weight !== null ? horse.weight : '-'}kg</span>
                        </div>
                        {/* 販売者履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">販売者:</span>
                          <span className="font-medium">{toArray(latestHistory.seller).join(' / ')}</span>
                        </div>
                        {/* オークション日履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">オークション日:</span>
                          <span className="font-medium">{toArray(latestHistory.auction_date).join(' / ')}</span>
                        </div>
                        {/* レース成績履歴 */}
                        <div className="flex justify-between">
                          <span className="text-gray-600">レース成績:</span>
                          <span className="font-medium">{toArray(latestHistory.race_record).join(' / ')}</span>
                        </div>
                        {/* オークションページリンク */}
                        {latestHistory.detail_url && (
                          <div className="flex justify-between items-center mt-2">
                            <span className="text-gray-600">オークションページ:</span>
                            <a 
                              href={latestHistory.detail_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:underline text-sm flex items-center"
                            >
                              詳細を見る
                              <svg className="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                              </svg>
                            </a>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 血統・病歴はそのまま */}
                    <div>
                      <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>血統</Typography>
                      <div className="space-y-2 text-sm">
                        <div className="flex">
                          <span className="text-gray-600 w-12">父：</span>
                          <span className="font-medium text-left">{horse.sire || '-'}</span>
                        </div>
                        <div className="flex">
                          <span className="text-gray-600 w-12">母：</span>
                          <span className="font-medium text-left">{horse.dam || '-'}</span>
                        </div>
                        <div className="flex">
                          <span className="text-gray-600 w-12">母父：</span>
                          <span className="font-medium text-left">{horse.dam_sire || '-'}</span>
                        </div>
                      </div>
                    </div>

                    {/* 病歴（血統の下に1箇所のみ表示） */}
                    {((latestHistory.disease_tags && String(latestHistory.disease_tags).trim() !== '') || 
                      (horse.disease_tags && String(horse.disease_tags).trim() !== '')) && (
                      <div>
                        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>病歴</Typography>
                        <div className="flex flex-wrap gap-2">
                          {(latestHistory.disease_tags || horse.disease_tags || '')
                            .split(',')
                            .filter(tag => tag.trim())
                            .map((tag, index) => (
                              <Badge key={index} variant="standard" className="bg-red-100 text-red-800 px-2 py-1 rounded">
                                {tag.trim()}
                              </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* 履歴テーブル表示 */}
            <Card className="mb-6">
              <CardHeader>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>全履歴</Typography>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="min-w-full text-sm border">
                    <thead>
                      <tr className="bg-gray-100">
                        <th className="px-2 py-1 border">回</th>
                        <th className="px-2 py-1 border">日付</th>
                        <th className="px-2 py-1 border">馬名</th>
                        <th className="px-2 py-1 border">性</th>
                        <th className="px-2 py-1 border">年齢</th>
                        <th className="px-2 py-1 border">販売者</th>
                        <th className="px-2 py-1 border">成績</th>
                        <th className="px-2 py-1 border">落札価格</th>
                        <th className="px-2 py-1 border">落札時賞金</th>
                      </tr>
                    </thead>
                    <tbody>
                      {horse.history.map((h, i) => (
                        <tr key={i} className="border-b">
                          <td className="px-2 py-1 border text-center">{i + 1}</td>
                          <td className="px-2 py-1 border">{h.auction_date}</td>
                          <td className="px-2 py-1 border">{h.name}</td>
                          <td className="px-2 py-1 border">{h.sex}</td>
                          <td className="px-2 py-1 border">{h.age}</td>
                          <td className="px-2 py-1 border">{h.seller}</td>
                          <td className="px-2 py-1 border">{h.race_record}</td>
                          <td className="px-2 py-1 border text-right">{displayPrice(h.sold_price, h.unsold)}</td>
                          <td className="px-2 py-1 border text-right">{formatPrize(h.total_prize_start)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>

            {/* コメント履歴（タブ切り替え） */}
            <Card className="mb-6">
              <CardHeader>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>コメント履歴</Typography>
              </CardHeader>
              <CardContent>
                <div className="flex gap-2 mb-2 overflow-x-auto pb-2">
                  {horse.history.map((h, i) => {
                    const hasComment = h.comment && h.comment.trim() !== '';
                    return (
                      <button
                        key={i}
                        className={`px-3 py-1 rounded whitespace-nowrap ${
                          activeTab === i 
                            ? 'bg-blue-600 text-white' 
                            : hasComment 
                              ? 'bg-gray-200 text-gray-700 hover:bg-gray-300' 
                              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                        onClick={() => setActiveTab(i)}
                        disabled={!hasComment}
                      >
                        {i + 1}回目 {!hasComment && '(コメントなし)'}
                      </button>
                    );
                  })}
                </div>
                <div className="border p-4 bg-gray-50 rounded-b min-h-[100px]">
                  {hasComments ? (
                    horse.history[activeTab]?.comment && horse.history[activeTab].comment.trim() !== '' ? (
                      <div className="prose max-w-none">
                        <p className="whitespace-pre-line text-gray-800">
                          {horse.history[activeTab].comment}
                        </p>
                        <div className="mt-2 text-sm text-gray-500">
                          {toArray(horse.history[activeTab]?.auction_date).join(' / ')}
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-full">
                        <p className="text-gray-500 italic">この回のコメントはありません</p>
                      </div>
                    )
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <p className="text-gray-500 italic">この馬のコメントは登録されていません</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* サイドバー - 価格・賞金情報 */}
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>落札価格</Typography>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* 主取り回数表示 */}
                {horse.unsold_count && horse.unsold_count > 0 && (
                  <div className="text-center text-blue-600 font-bold mb-2">主取り{horse.unsold_count}回</div>
                )}
                {/* 落札価格（最新） */}
                <div className="text-center">
                  <span className="text-red-600 text-3xl font-extrabold align-middle">{displayPrice(toArray(latestHistory.sold_price).slice(-1)[0], latestHistory.unsold)}</span>
                </div>
                {/* 履歴が2回以上ある場合のみ履歴表示 */}
                {toArray(latestHistory.sold_price).length > 1 && (
                  <div className="text-center mt-2">
                    {toArray(latestHistory.sold_price).map((sp, i) => (
                      <div key={i} className="text-lg font-bold mb-1">
                        <span className="text-red-600">{displayPrice(sp, horse.history[i]?.unsold)}</span>
                        <span className="text-xs text-gray-500 ml-2">{toArray(latestHistory.auction_date)[i] ?? ''}</span>
                      </div>
                    ))}
                    <div className="text-sm text-gray-600">落札価格履歴</div>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="mb-6">
              <CardHeader>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>賞金情報</Typography>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrize(Number(latestHistory.total_prize_start))}
                    </div>
                    <div className="text-xs text-gray-600">落札時</div>
                  </div>
                  <div>
                    <div className="text-lg font-semibold text-gray-900">
                      {formatPrize(Number(horse.total_prize_latest))}
                    </div>
                    <div className="text-xs text-gray-600">現在</div>
                  </div>
                </div>
                <div className="border-t pt-4">
                  <div className="text-center">
                    <div className={`text-xl font-bold ${horse.total_prize_latest - latestHistory.total_prize_start > 0 ? 'text-green-600' : horse.total_prize_latest - latestHistory.total_prize_start < 0 ? 'text-red-600' : 'text-gray-600'}`}> 
                      {(() => {
                        const start = Number(latestHistory.total_prize_start ?? 0);
                        const latestPrize = Number(horse.total_prize_latest ?? 0);
                        const diff = latestPrize - start;
                        if (diff === 0) {
                          return '0万円';
                        } else if (diff > 0) {
                          return `+${formatManYen(diff)}`;
                        } else {
                          return `-${formatManYen(Math.abs(diff))}`;
                        }
                      })()}
                    </div>
                    <div className="text-sm text-gray-600">オークション後の活躍</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* データ更新日 */}
            <Card>
              <CardHeader>
                <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>データ情報</Typography>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">作成日:</span>
                  <span>{formatDate(horse.created_at)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">更新日:</span>
                  <span>{formatDate(horse.updated_at)}</span>
                </div>

              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );

  // 戻るボタンのレンダリング
  const renderBackButton = () => (
    <Button 
      variant="outlined" 
      size="small"
      onClick={() => window.history.back()}
      className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
    >
      戻る
    </Button>
  );

  // オークション履歴をレンダリング
  const renderAuctionHistory = () => {
    if (!horse?.history?.length) {
      return <p className="text-gray-500">オークション履歴がありません</p>;
    }

    return (
      <div className="space-y-4">
        {horse.history.map((history, index) => (
          <div key={index} className="border-b pb-4 last:border-b-0 last:pb-0">
            <div className="flex justify-between items-start">
              <div>
                <Typography variant="h6" component="h4" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>{formatDate(history.auction_date)}</Typography>
                <p className="text-sm text-gray-500">
                  落札価格: {displayPrice(history.sold_price, history.unsold)}
                </p>
              </div>
              {history.detail_url && (
                <Button 
                  component={Link}
                  href={history.detail_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  variant="outlined" 
                  size="small"
                  className="whitespace-nowrap"
                >
                  詳細を見る
                </Button>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // コメントセクションをレンダリング
  const renderCommentSection = () => {
    if (!hasComments) {
      return null;
    }

    return (
      <Card>
        <CardHeader>
          <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>オークションコメント</Typography>
        </CardHeader>
        <CardContent>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            sx={{ mb: 2 }}
            aria-label="horse detail tabs"
          >
            <Tab label="基本情報" />
            <Tab label="血統情報" />
            <Tab label="取引履歴" />
          </Tabs>
          {horse.history.map((h, i) => (
            <div key={i}>
              {h.comment ? (
                <div className="whitespace-pre-line p-4 bg-gray-50 rounded-md">
                  {h.comment}
                </div>
              ) : (
                <p className="text-gray-500">コメントがありません</p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    );
  };

  // 馬の基本情報セクション
  const renderBasicInfo = () => {
    if (!horse) return null;
    
    return (
      <Card className="mb-6">
        <CardHeader>
          <div className="flex justify-between items-start">
            <div>
              <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1 }}>{horse.name}</Typography>
              <Typography variant="body2" color="text.secondary">
                {horse.sex} {horse.age}歳 | {horse.color} | {format(new Date(horse.birthday), 'yyyy年M月d日', { locale: ja })}
              </Typography>
            </div>
            <div className="flex space-x-2">
              {renderBackButton()}
            </div>
          </div>
        </CardHeader>
      </Card>
    );
  };

  // メインのレンダリング
  return (
    <div className="container mx-auto px-4 py-8">
      {renderBasicInfo()}
      
      {/* 馬の詳細情報セクション */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* 左カラム: 馬の画像 */}
        <div className="md:col-span-1">
          <Card className="mb-6">
            <div className="relative aspect-square">
              <HorseImage 
                src={horse.primary_image} 
                alt={horse.name}
                className="w-full h-full object-cover"
              />
            </div>
            <CardContent className="p-4">
              <div className="space-y-2">
                <div>
                  <span className="text-sm text-gray-500">父:</span>
                  <p className="font-medium">{horse.sire}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">母:</span>
                  <p className="font-medium">{horse.dam}</p>
                </div>
                <div>
                  <span className="text-sm text-gray-500">母の父:</span>
                  <p className="font-medium">{horse.dam_sire}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
        
        {/* 右カラム: 馬の情報 */}
        <div className="md:col-span-2">
          {/* オークション履歴 */}
          <Card className="mb-6">
            <CardHeader>
              <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>オークション履歴</Typography>
            </CardHeader>
            <CardContent>
              {renderAuctionHistory()}
            </CardContent>
          </Card>
          
          {/* コメントセクション */}
          {renderCommentSection()}
        </div>
      </div>
    </div>
  );
}