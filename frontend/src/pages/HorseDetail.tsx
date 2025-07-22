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
  sex: string[];
  age: (number | string)[];
  sire: string;
  dam: string;
  dam_sire: string;
  race_record: string;
  weight: number;
  total_prize_start: number | number[];
  total_prize_latest: number | number[];
  sold_price: number | number[];
  auction_date: string | string[];
  seller: string | string[];
  disease_tags: string;
  comment: string | string[];
  primary_image: string;
  created_at: string;
  updated_at: string;
  unsold_count?: number;
  jbis_url?: string;
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

  // 配列・単体どちらも対応して最新値を取得
  const getLastNumber = (val: number | number[] | undefined): number | undefined => {
    if (Array.isArray(val)) {
      if (val.length === 0) return undefined;
      return val[val.length - 1];
    }
    if (typeof val === 'number') return val;
    return undefined;
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
                    {horse.sex && horse.sex.length > 0 ? horse.sex[horse.sex.length-1] : '-'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    年齢
                  </Typography>
                  <Typography variant="body1">
                    {horse.age && horse.age.length > 0 ? horse.age[horse.age.length-1] : '-'}歳
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
                    {getLastNumber(horse.sold_price)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    落札日
                  </Typography>
                  <Typography variant="body1">
                    {horse.auction_date && Array.isArray(horse.auction_date) ? horse.auction_date[horse.auction_date.length - 1] : horse.auction_date || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    販売申込者
                  </Typography>
                  <Typography variant="body1">
                    {Array.isArray(horse.seller) ? (horse.seller.length > 0 ? horse.seller[horse.seller.length-1] : '-') : (horse.seller || '-')}
                  </Typography>
                </Grid>
              </Grid>
              {/* 落札価格履歴・落札日履歴（複数回のみ） */}
              {Array.isArray(horse.sold_price) && horse.sold_price.length > 1 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="body2" color="textSecondary">落札価格履歴</Typography>
                  <Typography variant="body1">
                    {horse.sold_price.map((price) => price).join(', ')}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>落札日履歴</Typography>
                  <Typography variant="body1">
                    {Array.isArray(horse.auction_date) ? horse.auction_date.join(', ') : '-'}
                  </Typography>
                </Box>
              )}
              {horse.unsold_count !== undefined && horse.unsold_count > 0 && (
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary" sx={{ color: '#b71c1c', fontWeight: 'bold' }}>
                    主取り{horse.unsold_count}回
                  </Typography>
                </Grid>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
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
                    出品時
                  </Typography>
                  <Typography variant="body1">
                    {getLastNumber(horse.total_prize_start)}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    現在
                  </Typography>
                  <Typography variant="body1">
                    {getLastNumber(horse.total_prize_latest)}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    成長率
                  </Typography>
                  <Typography 
                    variant="body1"
                    color={(() => {
                      const start = getLastNumber(horse.total_prize_start);
                      const latest = getLastNumber(horse.total_prize_latest);
                      return (typeof latest === 'number' && typeof start === 'number' && latest > start) ? 'green' : 'red';
                    })()}
                  >
                    {(() => {
                      const start = getLastNumber(horse.total_prize_start);
                      const latest = getLastNumber(horse.total_prize_latest);
                      if (typeof start !== 'number' || typeof latest !== 'number' || start === 0) return '-';
                      return `${((latest - start) / start * 100).toFixed(1)}%`;
                    })()}
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

        {Array.isArray(horse.comment) && horse.comment.length > 0 && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  コメント
                </Typography>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {Array.isArray(horse.comment) ? (horse.comment.length > 0 ? horse.comment[horse.comment.length-1] : '') : (horse.comment || '')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}

        {horse.jbis_url && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  外部リンク
                </Typography>
                <Typography variant="body1">
                  <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer">
                    JBISで詳細を見る
                  </a>
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default HorseDetail; 