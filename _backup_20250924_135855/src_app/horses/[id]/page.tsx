'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Tabs,
  Tab,
  Box,
  Button
} from '@mui/material';

// 型定義
interface RaceRecord {
  date: string;
  race_name: string;
  finish_position: string;
  prize_money: number;
  total_prize_money?: number;
}

interface BasicHorseInfo {
  id: string | number;
  name: string;
  sex: string;
  age: number;
  color?: string;
  birthday?: string;
  sire: string;
  dam: string;
  dam_sire: string;
  breeder?: string;
  owner?: string;
  trainer?: string;
  stable?: string;
  image_url?: string;
  jbis_url?: string;
  comment?: string;
  weight?: number | null;
  is_unsold?: boolean;
  sold_price: number | null;
  auction_date: string | null;
  seller?: string;
  unsold_count?: number;
  total_prize_latest?: number;
  disease_tags?: string | string[];
  primary_image?: string;
  race_records?: RaceRecord[];
}

interface HorseHistory {
  auction_date?: string | string[] | null;
  name?: string;
  sex?: string;
  age?: number | string;
  seller?: string;
  race_record?: string;
  comment?: string;
  sold_price?: number | number[] | null;
  total_prize_start?: number;
  unsold?: boolean;
  detail_url?: string;
  primary_image?: string;
  disease_tags?: string | string[];
  weight?: number | null;
}

interface Horse extends BasicHorseInfo {
  id: number;
  history: HorseHistory[];
  total_prize_latest?: number;
  total_prize_start?: number;
}

interface HorseDetailContentProps {
  horse: Horse;
}

// ヘルパー関数
const formatDate = (dateString: string): string => {
  if (!dateString) return '-';
  try {
    const date = new Date(dateString);
    return date.toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  } catch (e) {
    return '-';
  }
};

const displayPrice = (price: number | null | undefined, unsold: boolean = false): string => {
  if (unsold) return '未落札';
  if (price === null || price === undefined) return '-';
  return new Intl.NumberFormat('ja-JP').format(price) + '円';
};

const formatPrize = (val: number | string | null | undefined): string => {
  if (val === null || val === undefined) return '-';
  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) return '-';
  return new Intl.NumberFormat('ja-JP').format(num) + '万円';
};

// 馬詳細コンポーネント
const HorseDetailContent = ({ horse }: HorseDetailContentProps) => {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // 最新の履歴を取得
  const latestHistory = horse.history?.[0] || {};

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* メイン情報 */}
          <div className="lg:col-span-2">
            <Card className="mb-6">
              <CardHeader
                title={
                  <div className="flex justify-between items-center">
                    <Typography variant="h5" component="h1">
                      {horse.name || '不明'}
                    </Typography>
                    <Typography variant="subtitle1" color="textSecondary">
                      {horse.sex || ''} {horse.age || ''}歳
                    </Typography>
                  </div>
                }
              />
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Typography variant="subtitle2" color="textSecondary">父</Typography>
                    <Typography variant="body1">{horse.sire || '-'}</Typography>
                  </div>
                  <div>
                    <Typography variant="subtitle2" color="textSecondary">母</Typography>
                    <Typography variant="body1">{horse.dam || '-'}</Typography>
                  </div>
                  <div>
                    <Typography variant="subtitle2" color="textSecondary">母の父</Typography>
                    <Typography variant="body1">{horse.dam_sire || '-'}</Typography>
                  </div>
                  <div>
                    <Typography variant="subtitle2" color="textSecondary">セリ市</Typography>
                    <Typography variant="body1">
                      {formatDate(horse.auction_date as string)}
                    </Typography>
                  </div>
                  <div>
                    <Typography variant="subtitle2" color="textSecondary">落札価格</Typography>
                    <Typography variant="body1">
                      {displayPrice(horse.sold_price, horse.is_unsold)}
                    </Typography>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* サイドバー */}
          <div className="lg:col-span-1">
            <Card className="mb-6">
              <CardHeader
                title={
                  <Typography variant="h6" component="h3">
                    賞金情報
                  </Typography>
                }
              />
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <Typography variant="subtitle2" color="textSecondary">総賞金</Typography>
                    <Typography variant="body1">
                      {formatPrize(horse.total_prize_latest)}
                    </Typography>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

// メインページコンポーネント
export default function Page({ params }: { params: { id: string } }) {
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        setLoading(true);
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        const response = await fetch(`${apiUrl}/api/horses/${params.id}`);
        if (!response.ok) {
          throw new Error('馬データの取得に失敗しました');
        }
        const data = await response.json();
        setHorse(data as Horse);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id, router]);

  if (loading) {
    return <div>読み込み中...</div>;
  }

  if (error) {
    return <div>エラー: {error}</div>;
  }

  if (!horse) {
    return <div>馬のデータが見つかりませんでした</div>;
  }

  return <HorseDetailContent horse={horse} />;
}
