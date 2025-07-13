import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  CircularProgress,
  Alert
} from '@mui/material';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import axios from 'axios';

interface Statistics {
  total_horses: number;
  average_price: number;
  average_growth_rate: number;
  horses_with_growth_data: number;
  last_scraping_date: string | null;
  next_auction_date: string | null;
}

const Dashboard: React.FC = () => {
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      setLoading(true);
      const response = await axios.get('/statistics/');
      setStatistics(response.data);
    } catch (err) {
      setError('統計情報の取得に失敗しました');
      console.error('Error fetching statistics:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box>

      {loading ? (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : !statistics ? (
        <Alert severity="info">データがありません</Alert>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  総馬数
                </Typography>
                <Typography variant="h4">
                  {statistics.total_horses.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  平均落札価格
                </Typography>
                <Typography variant="h4">
                  ¥{statistics.average_price.toLocaleString()}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  平均成長率
                </Typography>
                <Typography variant="h4">
                  {statistics.average_growth_rate}%
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid item xs={12} md={3}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  成長データあり
                </Typography>
                <Typography variant="h4">
                  {statistics.horses_with_growth_data}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  データ概要
                </Typography>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={[
                    { name: '総馬数', value: statistics.total_horses },
                    { name: '成長データあり', value: statistics.horses_with_growth_data },
                  ]}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  スクレイピング情報
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    最後にスクレイピングした日
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {statistics.last_scraping_date || "データなし"}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    次回オークション開催日（予定）
                  </Typography>
                  <Typography variant="h6" color="secondary">
                    {statistics.next_auction_date || "未定"}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
};

export default Dashboard; 