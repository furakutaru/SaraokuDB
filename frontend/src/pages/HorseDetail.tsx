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
  Chip,
  Link,
  styled,
  GridTypeMap
} from '@mui/material';
import { transformHorseData } from '../utils/transformHorseData';
import axios from 'axios';
import { Horse } from '../types/horse';
import { OverridableComponent } from '@mui/material/OverridableComponent';

// Create a styled Grid component that includes the item prop by default
const StyledGrid = styled(Grid)({});

// Grid item component with proper TypeScript types
const GridItem: React.FC<{
  children: React.ReactNode;
  xs?: number | 'auto' | true | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  md?: number | 'auto' | true | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
  [key: string]: any;
}> = ({
  children,
  xs = 12,
  md,
  ...rest
}) => (
  <StyledGrid item xs={xs} md={md} {...rest}>
    {children}
  </StyledGrid>
);

// Grid container component with proper typing
const GridContainer: React.FC<{
  children: React.ReactNode;
  spacing?: number | string;
  [key: string]: any;
}> = ({
  children,
  spacing = 2,
  ...rest
}) => (
  <StyledGrid container spacing={spacing} {...rest}>
    {children}
  </StyledGrid>
);

const HorseDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [horse, setHorse] = useState<Horse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchHorse = async () => {
      try {
        const response = await fetch(`/api/horses/${id}`);
        if (!response.ok) {
          throw new Error('馬のデータの取得に失敗しました');
        }
        const data = await response.json();
        // Transform the API response to match the frontend format
        const transformedData = transformHorseData(data);
        setHorse(transformedData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'エラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchHorse();
    } else {
      setLoading(false);
      setError('馬のIDが指定されていません');
    }
  }, [id]);

  // 最新のオークション情報を取得
  const getLatestAuction = () => {
    if (!horse || !horse.auction_history || horse.auction_history.length === 0) {
      return { latestAuction: null, diseaseTags: [] as string[] };
    }
    const latestAuction = horse.auction_history[0];
    
    // Handle disease_tags which could be string, string[], or undefined
    const diseaseTags = (() => {
      if (!horse.disease_tags) return [] as string[];
      if (Array.isArray(horse.disease_tags)) return horse.disease_tags as string[];
      if (typeof horse.disease_tags === 'string') {
        return horse.disease_tags.split(',').map((tag: string) => tag.trim());
      }
      return [] as string[];
    })();

    return { latestAuction, diseaseTags };
  };

  const { latestAuction, diseaseTags } = getLatestAuction();
  
  // Ensure diseaseTags is always an array of strings
  const safeDiseaseTags: string[] = Array.isArray(diseaseTags) 
    ? diseaseTags.filter((tag): tag is string => typeof tag === 'string')
    : [];

  if (loading) {
    return <CircularProgress />;
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

      <GridContainer spacing={3}>
        {/* 馬体画像 */}
        {(horse.image_url || horse.primary_image) && (
          <GridItem xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  馬体画像
                </Typography>
                <Box sx={{ display: 'flex', justifyContent: 'center' }}>
                  <img 
                    src={horse.image_url || horse.primary_image} 
                    alt={`${horse.name}の馬体画像`}
                    style={{ 
                      maxWidth: '100%', 
                      maxHeight: '400px', 
                      objectFit: 'contain',
                      borderRadius: '4px'
                    }}
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                    }}
                  />
                </Box>
              </CardContent>
            </Card>
          </GridItem>
        )}
        <GridItem xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                基本情報
              </Typography>
              <GridContainer spacing={2}>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    性別
                  </Typography>
                  <Typography variant="body1">
                    {horse.sex || '-'}
                  </Typography>
                </GridItem>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    年齢
                  </Typography>
                  <Typography variant="body1">
                    {horse.age ? `${horse.age}歳` : '-'}
                  </Typography>
                </GridItem>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    馬体重
                  </Typography>
                  <Typography variant="body1">
                    {latestAuction?.weight || horse.weight || '-'}kg
                  </Typography>
                </GridItem>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    成績
                  </Typography>
                  <Typography variant="body1">
                    {horse.auction_history?.[0]?.comment || 'データなし'}
                  </Typography>
                </GridItem>
              </GridContainer>
            </CardContent>
          </Card>
        </GridItem>

        <GridItem xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                オークション情報
              </Typography>
              <GridContainer spacing={2}>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    落札価格
                  </Typography>
                  <Typography variant="body1">
                    {latestAuction?.sold_price ? `¥${Number(latestAuction.sold_price).toLocaleString()}` : '-'}
                  </Typography>
                </GridItem>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    落札日
                  </Typography>
                  <Typography variant="body1">
                    {latestAuction?.auction_date || horse.auction_date || '-'}
                  </Typography>
                </GridItem>
                <GridItem xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    売主
                  </Typography>
                  <Typography variant="body1">
                    {latestAuction?.seller || horse.seller || '-'}
                  </Typography>
                </GridItem>
              </GridContainer>
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
                <GridItem xs={12}>
                  <Typography variant="body2" color="textSecondary" sx={{ color: '#b71c1c', fontWeight: 'bold' }}>
                    主取り{horse.unsold_count}回
                  </Typography>
                </GridItem>
              )}
            </CardContent>
          </Card>
        </GridItem>

        <GridItem xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                血統情報
              </Typography>
              <GridContainer spacing={2}>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    父
                  </Typography>
                  <Typography variant="body1">
                    {horse.sire || '-'}
                  </Typography>
                </GridItem>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    母
                  </Typography>
                  <Typography variant="body1">
                    {horse.dam || '-'}
                  </Typography>
                </GridItem>
                <GridItem xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    母の父
                  </Typography>
                  <Typography variant="body1">
                    {horse.damsire || '-'}
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
                    総賞金（開始時）
                  </Typography>
                  <Typography variant="body1">
                    {latestAuction?.total_prize_start || horse.total_prize_start || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">
                    総賞金（最新）
                  </Typography>
                  <Typography variant="body1">
                    {latestAuction?.total_prize_latest || horse.total_prize_latest || '-'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">
                    成長率
                  </Typography>
                  <Typography 
                    variant="body1"
                    color={(() => {
                      const start = latestAuction?.total_prize_start || horse.total_prize_start;
                      const latest = latestAuction?.total_prize_latest || horse.total_prize_latest;
                      return (typeof latest === 'number' && typeof start === 'number' && latest > start) ? 'green' : 'red';
                    })()}
                  >
                    {(() => {
                      const start = latestAuction?.total_prize_start || horse.total_prize_start;
                      const latest = latestAuction?.total_prize_latest || horse.total_prize_latest;
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
              {diseaseTags.length > 0 ? (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {diseaseTags.map((disease: string, index: number) => (
                    <Chip key={index} label={disease} color="warning" size="small" />
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
                <Typography variant="body1" style={{ whiteSpace: 'pre-line' }}>
                  {horse.comment}
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
                  JBIS
                </Typography>
                <Typography variant="body1">
                  {horse.jbis_url ? (
                    <Typography variant="body1">Race records feature coming soon</Typography>
                  ) : '-'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

// レース記録の表示コンポーネント
const RaceRecordDisplay: React.FC<{ record: string | RaceRecordSummary | null }> = ({ record }) => {
  // レコードがnullまたはundefinedの場合
  if (!record) return <span>-</span>;
  
  // 文字列型の場合はそのまま表示
  if (typeof record === 'string') {
    return <span>{record}</span>;
  }
  
  // レコードがオブジェクトでない場合
  if (typeof record !== 'object') {
    return <span>-</span>;
  }
  
  // レコードが有効なRaceRecordSummaryオブジェクトかどうかをチェック
  const hasStatus = 'status' in record;
  
  // ステータスに基づいて表示を切り替え
  switch (record.status) {
    case 'unraced':
      return <span>未出走</span>;
    case 'broodmare':
      return <span>繁殖牝馬</span>;
    case 'active':
      // レース記録がある場合
      if (record.races !== undefined || record.wins !== undefined) {
        return (
          <span>
            {record.races ?? 0}戦{record.wins ?? 0}勝
            {(record.first !== undefined || record.second !== undefined || 
              record.third !== undefined || record.other !== undefined) && (
              <span style={{ fontSize: '0.9em', color: '#666' }}>
                [{record.first ?? 0}-{record.second ?? 0}-{record.third ?? 0}-{record.other ?? 0}]
              </span>
            )}
          </span>
        );
      }
      // サマリーがある場合はそれを使用
      if ('summary' in record && record.summary) {
        return <span>{record.summary}</span>;
      }
      return <span>-</span>;
    default:
      // 不明なステータスまたはステータスなし
      if ('summary' in record && record.summary) {
        return <span>{record.summary}</span>;
      }
      return <span>-</span>;
  }
};

export default HorseDetail; 