import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
  TextField,
  Grid,
  Switch,
  FormControlLabel,
  Chip
} from '@mui/material';
import { CloudDownload, Refresh } from '@mui/icons-material';
import axios from 'axios';

interface SchedulerStatus {
  is_running: boolean;
  next_scraping: string | null;
  should_run: boolean;
  scheduled_jobs: string[];
}

const ScrapingPage: React.FC = () => {
  const [scrapingLoading, setScrapingLoading] = useState(false);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [scrapingResult, setScrapingResult] = useState<string | null>(null);
  const [updateResult, setUpdateResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [auctionDate, setAuctionDate] = useState('');
  const [schedulerStatus, setSchedulerStatus] = useState<SchedulerStatus | null>(null);

  const handleScraping = async () => {
    try {
      setScrapingLoading(true);
      setError(null);
      setScrapingResult(null);

      const params: any = {};
      if (auctionDate) {
        params.auction_date = auctionDate;
      }

      const response = await axios.post('/scrape/', null, { params });
      setScrapingResult(`${response.data.count}頭の馬データを取得・保存しました`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'スクレイピングに失敗しました');
      console.error('Error during scraping:', err);
    } finally {
      setScrapingLoading(false);
    }
  };

  const handleUpdatePrizeMoney = async () => {
    try {
      setUpdateLoading(true);
      setError(null);
      setUpdateResult(null);

      const response = await axios.post('/update-prize-money/');
      setUpdateResult(`${response.data.updated_count}頭の馬の賞金情報を更新しました`);
    } catch (err: any) {
      setError(err.response?.data?.detail || '賞金更新に失敗しました');
      console.error('Error during prize money update:', err);
    } finally {
      setUpdateLoading(false);
    }
  };

  const fetchSchedulerStatus = async () => {
    try {
      const response = await axios.get('/scheduler/status');
      setSchedulerStatus(response.data);
    } catch (err) {
      console.error('Error fetching scheduler status:', err);
    }
  };

  const handleToggleScheduler = async () => {
    try {
      if (schedulerStatus?.is_running) {
        await axios.post('/scheduler/stop');
      } else {
        await axios.post('/scheduler/start');
      }
      fetchSchedulerStatus();
    } catch (err) {
      setError('スケジューラーの操作に失敗しました');
    }
  };

  useEffect(() => {
    fetchSchedulerStatus();
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        スクレイピング管理
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                新規データ取得
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                楽天サラブレッドオークションから新しい馬データを取得します。
                木曜オークションは木曜23:59、日曜オークションは日曜23:59に実行してください。
              </Typography>
              
              <TextField
                label="開催日（YYYY-MM-DD）"
                value={auctionDate}
                onChange={(e) => setAuctionDate(e.target.value)}
                placeholder="例: 2024-01-15"
                fullWidth
                sx={{ mb: 2 }}
              />
              
              <Button
                variant="contained"
                startIcon={<CloudDownload />}
                onClick={handleScraping}
                disabled={scrapingLoading}
                fullWidth
              >
                {scrapingLoading ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    スクレイピング中...
                  </>
                ) : (
                  'スクレイピング実行'
                )}
              </Button>

              {scrapingResult && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {scrapingResult}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                賞金情報更新
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                既存の馬データの最新賞金情報をnetkeibaから取得して更新します。
                時間がかかる場合があります。
              </Typography>
              
              <Button
                variant="contained"
                color="secondary"
                startIcon={<Refresh />}
                onClick={handleUpdatePrizeMoney}
                disabled={updateLoading}
                fullWidth
              >
                {updateLoading ? (
                  <>
                    <CircularProgress size={20} sx={{ mr: 1 }} />
                    更新中...
                  </>
                ) : (
                  '賞金情報更新'
                )}
              </Button>

              {updateResult && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  {updateResult}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                自動スケジューラー
              </Typography>
              
              <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={schedulerStatus?.is_running || false}
                      onChange={handleToggleScheduler}
                      color="primary"
                    />
                  }
                  label="自動実行を有効にする"
                />
                <Chip
                  label={schedulerStatus?.is_running ? "実行中" : "停止中"}
                  color={schedulerStatus?.is_running ? "success" : "default"}
                  size="small"
                />
              </Box>

              {schedulerStatus?.next_scraping && (
                <Typography variant="body2" color="textSecondary" sx={{ mb: 1 }}>
                  <strong>次のスクレイピング予定:</strong> {schedulerStatus.next_scraping}
                </Typography>
              )}

              <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                <strong>スケジュール:</strong>
              </Typography>
              <Box sx={{ ml: 2 }}>
                {schedulerStatus?.scheduled_jobs.map((job, index) => (
                  <Typography key={index} variant="body2" color="textSecondary" sx={{ mb: 0.5 }}>
                    • {job}
                  </Typography>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                スクレイピングスケジュール（手動実行時）
              </Typography>
              <Typography variant="body2" color="textSecondary">
                <strong>木曜オークション:</strong> 木曜23:59に自動実行されます。手動実行の場合は木曜夜にスクレイピングを実行してください。
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                <strong>日曜オークション:</strong> 日曜23:59に自動実行されます。手動実行の場合は日曜夜にスクレイピングを実行してください。
              </Typography>
              <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                <strong>注意:</strong> スクレイピングはサーバーに負荷をかけるため、適切な間隔を空けて実行してください。
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ScrapingPage; 