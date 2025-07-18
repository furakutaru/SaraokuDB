import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import Link from 'next/link';
import HorseImage from '@/components/HorseImage';
import fs from 'fs';
import path from 'path';

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: number;
  sold_price: number;
  seller: string;
  total_prize_start: number;
  total_prize_latest: number;
  sire: string;
  dam: string;
  dam_sire: string;
  comment: string;
  weight: number;
  race_record: string;
  primary_image: string;
  auction_date: string;
  disease_tags: string;
  netkeiba_url: string;
  created_at: string;
  updated_at: string;
  unsold_count: number; // 追加: 主取り馬の数
}

interface Metadata {
  last_updated: string;
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
  next_auction_date: string;
}

interface HorseData {
  metadata: Metadata;
  horses: Horse[];
}

// データファイルを読み込む
function loadHorseData(): HorseData {
  try {
    const dataPath = path.join(process.cwd(), 'public', 'data', 'horses.json');
    const data = fs.readFileSync(dataPath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('データファイルの読み込みに失敗しました:', error);
    // フォールバックデータ
    return {
      metadata: {
        last_updated: new Date().toISOString(),
        total_horses: 0,
        average_price: 0,
        average_growth_rate: 0,
        horses_with_growth_data: 0,
        next_auction_date: new Date().toISOString().split('T')[0]
      },
      horses: []
    };
  }
}

// 賞金表示用関数を追加
const formatPrize = (val: number | null | undefined) => {
  if (val === null || val === undefined) return '-';
  return `${(val / 10000).toFixed(1)}万円`;
};

// 落札価格表示用関数を追加
const formatPrice = (price: number | null | undefined) => {
  if (price === null || price === undefined) return '-';
  return '¥' + price.toLocaleString();
};

// 直近の火曜または土曜18:30を計算する関数を追加
function getNextScrapingDate(): string {
  const now = new Date();
  const day = now.getDay(); // 0:日, 1:月, 2:火, 3:水, 4:木, 5:金, 6:土
  const hour = now.getHours();
  const minute = now.getMinutes();
  // 火曜18:30
  let nextTuesday = new Date(now);
  nextTuesday.setDate(now.getDate() + ((2 - day + 7) % 7));
  nextTuesday.setHours(18, 30, 0, 0);
  // 土曜18:30
  let nextSaturday = new Date(now);
  nextSaturday.setDate(now.getDate() + ((6 - day + 7) % 7));
  nextSaturday.setHours(18, 30, 0, 0);
  // どちらも今より前なら+7日
  if (nextTuesday < now) nextTuesday.setDate(nextTuesday.getDate() + 7);
  if (nextSaturday < now) nextSaturday.setDate(nextSaturday.getDate() + 7);
  // 直近を選ぶ
  const next = nextTuesday < nextSaturday ? nextTuesday : nextSaturday;
  return `${next.getFullYear()}-${(next.getMonth()+1).toString().padStart(2,'0')}-${next.getDate().toString().padStart(2,'0')} 18:30`;
}

export default function Home() {
  const data = loadHorseData();
  const { metadata, horses } = data;

  // 成長率データ
  const growthData = horses
    .filter((h: Horse) => h.total_prize_start > 0 && h.total_prize_latest > 0)
    .map((h: Horse) => ({
      name: h.name,
      growth: ((h.total_prize_latest - h.total_prize_start) / h.total_prize_start * 100)
    }))
    .sort((a: any, b: any) => b.growth - a.growth)
    .slice(0, 10);

  // 総馬数のカウントを主取り馬を除外した数に修正
  const validHorses = horses.filter(h => !h.unsold_count || h.unsold_count === 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">サラブレッドオークションDB</h1>
              <p className="text-gray-600">最終更新: {new Date(metadata.last_updated).toLocaleString('ja-JP')}</p>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/dashboard">
                <Button variant="default" className="bg-green-600 hover:bg-green-700 text-white font-bold px-6 py-2 rounded shadow">解析</Button>
              </Link>
              <Link href="/horses" className="text-blue-600 hover:text-blue-800 font-medium">
                馬一覧
              </Link>
              <div className="text-right">
                <p className="text-sm text-gray-500">次回スクレイピング</p>
                <p className="text-lg font-semibold text-blue-600">{getNextScrapingDate()}</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* メインコンテンツ */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 統計カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">総馬数</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{validHorses.length.toLocaleString()}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均落札価格</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatPrice(metadata.average_price)}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">平均成長率</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metadata.average_growth_rate}%</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">成長データあり</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{metadata.horses_with_growth_data}</div>
            </CardContent>
          </Card>
        </div>

        {/* 成長率データ */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>成長率トップ10</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {growthData.map((item: any, index: number) => (
                <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                  <span className="font-medium">{item.name}</span>
                  <span className="text-green-600 font-semibold">{item.growth.toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 馬一覧 */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle>馬一覧</CardTitle>
              <Link href="/horses">
                <Button variant="outline" size="sm" className="text-white bg-blue-600 hover:bg-blue-700 border-blue-600">
                  すべて見る
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {horses.filter(h => !h.unsold_count || h.unsold_count === 0).slice(0, 5).map((horse: Horse) => (
                <Link key={horse.id} href={`/horses/${horse.id}`}>
                  <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer">
                    <div className="flex items-center space-x-3">
                      {horse.primary_image && (
                        <HorseImage
                          src={horse.primary_image}
                          alt={horse.name}
                          className="w-12 h-12 object-contain rounded bg-gray-100"
                        />
                      )}
                      <div>
                        <h4 className="font-semibold">{horse.name}</h4>
                        <p className="text-sm text-gray-600">{horse.sex} {horse.age}歳</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-green-600">{formatPrice(horse.sold_price)}</p>
                      <p className="text-sm text-gray-500">{horse.seller}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
