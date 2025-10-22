'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { Card, CardContent, Typography } from '@mui/material';

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
  const params = useParams<{ id: string }>();
  
  // params が null の場合はエラーを表示
  if (!params) {
    return (
      <div className="p-4">
        <p className="text-red-500">エラー: パラメータが正しく取得できませんでした</p>
      </div>
    );
  }
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
        const response = await fetch('/data/horses_combined.json');
        
        if (!response.ok) {
          throw new Error('データの取得に失敗しました');
        }

        const data = await response.json();
        console.log('データを取得しました', data);

        const horseData = data.horses?.find((h: any) => 
          h.id === horseId || h.id?.toString() === horseId.toString()
        );

        if (!horseData) {
          throw new Error('指定された馬のデータが見つかりませんでした');
        }

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
    return <div>読み込み中...</div>;
  }

  if (error) {
    return <div>エラー: {error}</div>;
  }

  if (!horse) {
    return <div>馬のデータが見つかりませんでした</div>;
  }

  return (
    <div style={{ padding: '20px' }}>
      <h1>馬の詳細情報（シンプル版）</h1>
      <Card sx={{ maxWidth: 600, margin: '0 auto' }}>
        <CardContent>
          <Typography variant="h5" component="div" gutterBottom>
            {horse.name}
          </Typography>
          <Typography color="text.secondary" gutterBottom>
            {horse.sex} | {horse.age}歳
          </Typography>
          
          {horse.weight && (
            <Typography variant="body1" sx={{ mt: 2 }}>
              体重: {horse.weight} kg
            </Typography>
          )}
          
          {horse.seller && (
            <Typography variant="body1" sx={{ mt: 1 }}>
              販売者: {horse.seller}
            </Typography>
          )}
          
          {horse.comment && (
            <div style={{ marginTop: '16px', padding: '16px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
              <Typography variant="subtitle2" gutterBottom>
                コメント:
              </Typography>
              <Typography variant="body2" whiteSpace="pre-line">
                {horse.comment}
              </Typography>
            </div>
          )}
        </CardContent>
      </Card>
      
      <div style={{ marginTop: '20px' }}>
        <a href={`/horses/${params.id}`}>元のページに戻る</a>
      </div>
    </div>
  );
}
