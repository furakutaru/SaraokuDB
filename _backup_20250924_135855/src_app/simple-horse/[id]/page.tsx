'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, Typography, Button, Box } from '@mui/material';

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: string;
  weight?: number;
  comment?: string;
  seller?: string;
  // 他の必要なフィールドを追加
}

export default function SimpleHorsePage() {
  const params = useParams();
  const router = useRouter();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHorseData = async () => {
      try {
        const horseId = Number(params.id);
        if (!horseId || isNaN(horseId)) {
          throw new Error('無効な馬IDです');
        }

        console.log('馬データを取得中...');
        // 相対パスで直接JSONファイルを取得
        const response = await fetch('/data/horses_combined.json', {
          cache: 'no-store',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        
        if (!response.ok) {
          const errorText = await response.text();
          console.error('データの取得に失敗しました:', {
            status: response.status,
            statusText: response.statusText,
            error: errorText
          });
          throw new Error(`データの取得に失敗しました (${response.status})`);
        }

        const data = await response.json();
        console.log('データを取得しました', {
          dataKeys: Object.keys(data),
          hasHorses: Array.isArray(data.horses),
          horsesCount: data.horses?.length,
          firstHorseId: data.horses?.[0]?.id,
          firstHorseName: data.horses?.[0]?.name
        });

        // デバッグ用に全ての馬のIDをログ出力
        console.log('利用可能な馬のID（先頭10件）:', 
          data.horses.slice(0, 10).map((h: any) => h.id).join(', ')
        );

        // 文字列のIDを数値に変換して比較
        const horseData = data.horses?.find((h: any) => {
          const id = typeof h.id === 'string' ? parseInt(h.id, 10) : h.id;
          return id === horseId;
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

        setHorse({
          id: horseData.id,
          name: horseData.name,
          sex: horseData.sex,
          age: horseData.age,
          weight: horseData.weight,
          comment: horseData.comment,
          seller: horseData.seller
        });
      } catch (err) {
        console.error('エラーが発生しました:', err);
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    fetchHorseData();
  }, [params.id]);

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
      <Button 
        variant="outlined" 
        onClick={() => router.push(`/horses/${horse.id}`)}
        sx={{ mb: 2 }}
      >
        ← 元のページに戻る
      </Button>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            {horse.name}
          </Typography>
          <Typography color="text.secondary" gutterBottom>
            {horse.sex} | {horse.age}歳
          </Typography>
          
          {horse.weight && (
            <Typography variant="body1" sx={{ mt: 2 }}>
              <strong>体重:</strong> {horse.weight} kg
            </Typography>
          )}
          
          {horse.seller && (
            <Typography variant="body1" sx={{ mt: 1 }}>
              <strong>販売者:</strong> {horse.seller}
            </Typography>
          )}
          
          {horse.comment && (
            <Box sx={{ mt: 3, p: 2, backgroundColor: '#f5f5f5', borderRadius: 1 }}>
              <Typography variant="subtitle1" gutterBottom>
                <strong>コメント:</strong>
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
