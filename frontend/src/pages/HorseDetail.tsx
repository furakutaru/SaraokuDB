import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Box,
  CircularProgress,
  Alert,
  Chip
} from '@mui/material';
import axios from 'axios';

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: number;
  sire: string;
  dam: string;
  dam_sire: string;
  race_record: string;
  weight: number;
  total_prize_start: number;
  total_prize_latest: number;
  sold_price: number;
  auction_date: string;
  seller: string;
  disease_tags: string;
  comment: string;
  netkeiba_url: string;
  primary_image: string;
  created_at: string;
  updated_at: string;
}

const HorseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchHorse(parseInt(id));
    }
  }, [id]);

  const fetchHorse = async (horseId: number) => {
    try {
      setLoading(true);
      const response = await axios.get(`/horses/${horseId}`);
      setHorse(response.data);
    } catch (err) {
      setError('馬データの取得に失敗しました');
      console.error('Error fetching horse:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price: number) => {
    if (price >= 10000) {
      return `¥${(price / 10000).toLocaleString()}万円`;
    }
    return `¥${price.toLocaleString()}`;
  };

  const calculateGrowthRate = (start: number, latest: number) => {
    if (start === 0) return 0;
    return ((latest - start) / start * 100).toFixed(1);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!horse) {
    return <Alert severity="info">馬が見つかりません</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        {horse.name}
      </Typography>

      <Grid container spacing={3}>
        {/* 馬体画像 */}
        {horse.primary_image && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  馬体画像
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <img 
                    src={horse.primary_image} 
                    alt={`${horse.name}の馬体画像`}
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: '400px', 
                      objectFit: 'contain',
                      borderRadius: '8px'
                    }}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        )}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                基本情報
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    性別
                  </Typography>
                  <Typography variant="body1">
                    {horse.sex}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    年齢
                  </Typography>
                  <Typography variant="body1">
                    {horse.age}歳
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    馬体重
                  </Typography>
                  <Typography variant="body1">
                    {horse.weight}kg
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    成績
                  </Typography>
                  <Typography variant="body1">
                    {horse.race_record}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                オークション情報
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    落札価格
                  </Typography>
                  <Typography variant="body1">
                    {formatPrice(horse.sold_price)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    開催日
                  </Typography>
                  <Typography variant="body1">
                    {horse.auction_date}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    販売申込者
                  </Typography>
                  <Typography variant="body1">
                    {horse.seller}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                血統情報
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="textSecondary">
                    父
                  </Typography>
                  <Typography variant="body1">
                    {horse.sire}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="textSecondary">
                    母
                  </Typography>
                  <Typography variant="body1">
                    {horse.dam}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="textSecondary">
                    母父
                  </Typography>
                  <Typography variant="body1">
                    {horse.dam_sire}
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                賞金情報
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    出品時賞金
                  </Typography>
                  <Typography variant="body1">
                    {horse.total_prize_start}万円
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    最新賞金
                  </Typography>
                  <Typography variant="body1">
                    {horse.total_prize_latest}万円
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    成長率
                  </Typography>
                  <Typography 
                    variant="body1"
                    color={horse.total_prize_latest > horse.total_prize_start ? 'green' : 'red'}
                  >
                    {calculateGrowthRate(horse.total_prize_start, horse.total_prize_latest)}%
                  </Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                疾病情報
              </Typography>
              {horse.disease_tags ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {horse.disease_tags.split(',').map((disease, index) => (
                    <Chip key={index} label={disease.trim()} color="warning" size="small" />
                  ))}
                </Box>
              ) : (
                <Typography variant="body2" color="textSecondary">
                  疾病情報なし
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>

        {horse.comment && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  コメント
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {horse.comment}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                外部リンク
              </Typography>
              {horse.netkeiba_url && (
                <Typography variant="body1">
                  <a href={horse.netkeiba_url} target="_blank" rel="noopener noreferrer">
                    netkeibaで詳細を見る
                  </a>
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default HorseDetail; 