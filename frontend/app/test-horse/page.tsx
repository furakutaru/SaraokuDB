'use client';

import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import { Card, CardContent, Typography, Button, Box, Chip } from '@mui/material';

interface RaceRecords {
  total_prize_money: number;
  last_race_date: string | null;
  last_prize_update: string;
  starts?: number;
  wins?: number;
  seconds?: number;
  thirds?: number;
  [key: string]: any;
}

interface BasicInfo {
  name?: string;
  sex?: string;
  age?: number;
  sire?: string;
  dam?: string;
  damsire?: string;
  weight?: number;
  race_records?: RaceRecords;
  seller?: string;
  owner?: string;
  breeder?: string;
  trainer?: string;
  location?: string;
  [key: string]: any;
}

interface Horse {
  id: string;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  damsire: string;
  weight?: number;
  race_records?: RaceRecords;
  sold_price?: number | null;
  comment?: string;
  disease_tags?: string[];
  seller?: string;
  auction_url?: string;
  jbis_url?: string;
  image_url?: string;
  owner?: string;
  breeder?: string;
  trainer?: string;
  location?: string;
  basic_info?: BasicInfo;
  is_retired?: boolean;
  retirement_date?: string | null;
  auction_date?: string | null;
  is_unsold?: boolean;
}

export default function TestHorsePage() {
  const searchParams = useSearchParams();
  // searchParams が null の場合はデフォルト値を使用
  const horseId = searchParams?.get('id') || '14927';
  
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        console.log('馬データを取得中...');
        const response = await fetch('/data/horses_combined.json');
        
        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const data = await response.json();
        console.log('データを取得しました', {
          dataKeys: Object.keys(data),
          hasHorses: Array.isArray(data.horses),
          horsesCount: data.horses?.length,
          firstHorseId: data.horses?.[0]?.id,
          firstHorseName: data.horses?.[0]?.name
        });

        // 文字列のIDを数値に変換して比較
        const horseData = data.horses?.find((h: any) => {
          const id = typeof h.id === 'string' ? parseInt(h.id, 10) : h.id;
          return id === parseInt(horseId, 10);
        });

        if (!horseData) {
          console.error('馬データが見つかりませんでした。検索したID:', horseId);
          console.error('利用可能な馬の数:', data.horses?.length);
          console.error('先頭の馬のIDと名前:', 
            data.horses[0]?.id, 
            data.horses[0]?.name
          );
          throw new Error(`ID: ${horseId} の馬データが見つかりませんでした`);
        }
        
        console.log('マッチした馬データ:', horseData);
        // コメントから体重情報を抽出する関数
        const extractWeightFromComment = (comment: string): number | null => {
          if (!comment) return null;
          // 例: 「馬体重458kg」のようなパターンを検索
          const weightMatch = comment.match(/馬体重(?:\s*[（(]?\s*)(\d+)(?:\s*[）)]?\s*)(?:kg|キロ|㎏)/i);
          if (weightMatch && weightMatch[1]) {
            return parseInt(weightMatch[1], 10);
          }
          return null;
        };
        
        // 基本情報をマージ
        const mergedData = {
          ...horseData.basic_info,
          ...horseData,
          // 基本情報とトップレベルの情報をマージ（トップレベルを優先）
          id: horseData.id,
          name: horseData.name || horseData.basic_info?.name || '不明',
          sex: horseData.sex || horseData.basic_info?.sex || '不明',
          age: horseData.age || horseData.basic_info?.age || 0,
          sire: horseData.sire || horseData.basic_info?.sire || '不明',
          dam: horseData.dam || horseData.basic_info?.dam || '不明',
          damsire: horseData.damsire || horseData.basic_info?.damsire || '不明',
          // 体重情報を取得（複数のソースから順に試す）
          weight: horseData.weight || 
                 horseData.basic_info?.weight ||
                 (horseData.comment ? extractWeightFromComment(horseData.comment) : null),
          // レース記録をマージ
          race_records: {
            ...(horseData.basic_info?.race_records || {}),
            ...(horseData.race_records || {})
          },
          // その他の情報
          sold_price: horseData.sold_price,
          comment: horseData.comment,
          disease_tags: horseData.disease_tags || [],
          seller: horseData.seller || horseData.basic_info?.seller || '不明',
          owner: horseData.owner || horseData.basic_info?.owner,
          breeder: horseData.breeder || horseData.basic_info?.breeder,
          trainer: horseData.trainer || horseData.basic_info?.trainer,
          location: horseData.location || horseData.basic_info?.location,
          auction_url: horseData.auction_url,
          jbis_url: horseData.jbis_url,
          image_url: horseData.image_url,
          is_retired: horseData.is_retired,
          retirement_date: horseData.retirement_date,
          auction_date: horseData.auction_date,
          is_unsold: horseData.is_unsold
        };
        
        setHorse(mergedData);
      } catch (err) {
        console.error('エラーが発生しました:', err);
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorseData();
  }, [horseId]);

  if (loading) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>読み込み中...</Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography color="error">エラー: {error}</Typography>
        <Button 
          variant="contained" 
          onClick={() => window.location.reload()}
          sx={{ mt: 2 }}
        >
          再読み込み
        </Button>
      </Box>
    );
  }

  if (!horse) {
    return (
      <Box sx={{ p: 3, textAlign: 'center' }}>
        <Typography>馬のデータが見つかりませんでした</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box sx={{ display: 'flex', gap: 3 }}>
            {/* 左カラム: 基本情報 */}
            <Box sx={{ flex: 1 }}>
              <Typography variant="h5" component="div" gutterBottom>
                {horse.name}
              </Typography>
              
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                <Box>
                  <Typography variant="body2" color="text.secondary">性別</Typography>
                  <Typography variant="body1">{horse.sex}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">年齢</Typography>
                  <Typography variant="body1">{horse.age}歳</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">父</Typography>
                  <Typography variant="body1">{horse.sire}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">母</Typography>
                  <Typography variant="body1">{horse.dam}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">母の父</Typography>
                  <Typography variant="body1">{horse.damsire}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">馬体重</Typography>
                  <Typography variant="body1">{horse.weight ? `${horse.weight}kg` : '-'}</Typography>
                </Box>
              </Box>
              
              <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mb: 2 }}>
                {/* 賞金 */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">賞金</Typography>
                  <Typography variant="body1">
                    {horse.race_records?.total_prize_money 
                      ? `${horse.race_records.total_prize_money.toLocaleString()}円` 
                      : 'データなし'}
                  </Typography>
                </Box>
                
                {/* 落札価格 */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">
                    {horse.is_unsold ? '未落札' : '落札価格'}
                  </Typography>
                  <Typography variant="body1">
                    {horse.sold_price !== null && horse.sold_price !== undefined 
                      ? `${horse.sold_price.toLocaleString()}円` 
                      : horse.is_unsold ? '未落札' : 'データなし'}
                  </Typography>
                </Box>

                {/* 販売者 */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">販売者</Typography>
                  <Typography variant="body1">{horse.seller || '不明'}</Typography>
                </Box>

                {/* 主取り */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">主取り</Typography>
                  <Typography variant="body1">{horse.owner || '不明'}</Typography>
                </Box>

                {/* 調教師 */}
                {horse.trainer && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">調教師</Typography>
                    <Typography variant="body1">{horse.trainer}</Typography>
                  </Box>
                )}

                {/* 戦績 */}
                {(horse.race_records?.starts !== undefined || 
                  horse.race_records?.wins !== undefined || 
                  horse.race_records?.seconds !== undefined || 
                  horse.race_records?.thirds !== undefined) && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">戦績</Typography>
                    <Typography variant="body1">
                      {horse.race_records?.starts || 0}戦 {horse.race_records?.wins || 0}勝
                      {horse.race_records?.seconds !== undefined ? ` ${horse.race_records.seconds}着` : ''}
                      {horse.race_records?.thirds !== undefined ? `-${horse.race_records.thirds}着` : ''}
                    </Typography>
                  </Box>
                )}

                {/* 競走馬登録 */}
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">競走馬登録</Typography>
                  <Typography variant="body1">
                    {horse.is_retired ? '引退' : horse.race_records?.starts !== undefined ? '登録済み' : '未登録'}
                    {horse.retirement_date && ` (${new Date(horse.retirement_date).getFullYear()}.${(new Date(horse.retirement_date).getMonth() + 1).toString().padStart(2, '0')}引退)`}
                  </Typography>
                </Box>

                {/* オークション日 */}
                {horse.auction_date && (
                  <Box>
                    <Typography variant="subtitle2" color="text.secondary">オークション日</Typography>
                    <Typography variant="body1">
                      {new Date(horse.auction_date).toLocaleDateString('ja-JP', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        weekday: 'short'
                      })}
                    </Typography>
                  </Box>
                )}
              </Box>
              
              {horse.disease_tags && horse.disease_tags.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="error">疾病情報</Typography>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {horse.disease_tags.map((disease, index) => (
                      <Chip key={index} label={disease} color="error" size="small" />
                    ))}
                  </Box>
                </Box>
              )}
              
              <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                {horse.jbis_url && (
                  <Button 
                    variant="outlined" 
                    size="small" 
                    href={horse.jbis_url} 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    JBIS
                  </Button>
                )}
                {horse.auction_url && (
                  <Button 
                    variant="outlined" 
                    size="small" 
                    href={horse.auction_url} 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    オークションページ
                  </Button>
                )}
              </Box>
            </Box>
            
            {/* 右カラム: 画像 */}
            {horse.image_url && (
              <Box sx={{ width: 300, flexShrink: 0 }}>
                <img 
                  src={horse.image_url} 
                  alt={horse.name}
                  style={{ 
                    width: '100%', 
                    height: 'auto',
                    borderRadius: '4px',
                    objectFit: 'cover'
                  }} 
                />
              </Box>
            )}
          </Box>
          
          {horse.comment && (
            <Box sx={{ mt: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                コメント
              </Typography>
              <Typography variant="body2" whiteSpace="pre-line">
                {horse.comment}
              </Typography>
            </Box>
          )}
        </CardContent>
      </Card>
    </Box>
  );
}
