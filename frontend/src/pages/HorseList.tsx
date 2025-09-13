import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Pagination,
  Button
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import AddIcon from '@mui/icons-material/Add';

import { Horse } from '../types/horse';
import { horseApi, statsApi } from '../utils/api';
import { transformHorseArray } from '../utils/transformHorseData';

interface HorseListProps {
  // 必要に応じてプロパティを追加
}

const HorseList: React.FC = () => {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [auctionDates, setAuctionDates] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    fetchHorses();
    fetchAuctionDates();
  }, [page, selectedDate]);

  const fetchHorses = async () => {
    setLoading(true);
    setError(null);
    try {
      // バックエンドAPIからデータを取得
      const response = await fetch('http://localhost:8000/api/test/horses');
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      
      const data = await response.json();
      
      // データを変換（必要な場合）
      const transformedHorses = transformHorseArray(data.horses || []);
      setHorses(transformedHorses);
      
      // ページネーション情報はAPIから取得するか、デフォルト値を設定
      setTotalPages(1);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching horses:', error);
      setError('馬のデータの取得中にエラーが発生しました');
      setLoading(false);
    }
  };

  const fetchAuctionDates = async () => {
    try {
      const dates = await statsApi.getAuctionDates();
      // 日付を重複なくソートしてセット
      const uniqueDates = Array.from(new Set(Array.isArray(dates) ? dates : []))
        .sort()
        .reverse(); // 新しい日付順にソート
      setAuctionDates(uniqueDates as string[]);
    } catch (err) {
      console.error('Error fetching auction dates:', err);
      setAuctionDates([]);
    }
  };

  // 検索はバックエンドで行うため、クライアントサイドでのフィルタリングは行わない
  const filteredHorses = horses || [];
  
  // 検索フィールドの変更時に検索を実行
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    // 検索テキストが変更されたら1ページ目に戻る
    setPage(1);
  };

  // オークション日付の変更時に検索を実行
  const handleAuctionDateChange = (event: React.ChangeEvent<{ value: unknown }> | any) => {
    setSelectedDate(event.target.value as string);
    setPage(1);
  };
  
  // ページ変更時のハンドラ
  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box my={4}>
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={fetchHorses}
        >
          再試行
        </Button>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          馬一覧
        </Typography>
        <Button 
          variant="contained" 
          color="primary" 
          startIcon={<AddIcon />}
          component={RouterLink}
          to="/horses/new"
        >
          新規登録
        </Button>
      </Box>
      
      <Box sx={{ mb: 3, display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <TextField
          label="馬名で検索"
          value={searchTerm}
          onChange={handleSearchChange}
          sx={{ minWidth: 300, mb: { xs: 2, md: 0 } }}
          placeholder="馬名を入力"
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              fetchHorses();
            }
          }}
        />
        <FormControl sx={{ minWidth: 200, mb: { xs: 2, md: 0 } }}>
          <InputLabel id="auction-date-label">オークション日</InputLabel>
          <Select
            labelId="auction-date-label"
            id="auction-date"
            value={selectedDate}
            label="オークション日"
            onChange={handleAuctionDateChange}
            disabled={loading}
          >
            <MenuItem value="">すべての日付</MenuItem>
            {auctionDates.map((date) => {
              // 日付のフォーマット（必要に応じて調整）
              const formattedDate = new Date(date).toLocaleDateString('ja-JP', {
                year: 'numeric',
                month: 'long',
                day: 'numeric',
                weekday: 'short'
              });
              return (
                <MenuItem key={date} value={date}>
                  {formattedDate}
                </MenuItem>
              );
            })}
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper} sx={{ mt: 3, overflowX: 'auto' }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>馬名</TableCell>
              <TableCell>性別</TableCell>
              <TableCell>年齢</TableCell>
              <TableCell>父</TableCell>
              <TableCell>母</TableCell>
              <TableCell>母父</TableCell>
              <TableCell>落札価格</TableCell>
              <TableCell>オークション日</TableCell>
              <TableCell>アクション</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && filteredHorses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                  <CircularProgress />
                  <Box mt={2}>データを読み込んでいます...</Box>
                </TableCell>
              </TableRow>
            ) : filteredHorses.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center" sx={{ py: 4 }}>
                  該当する馬が見つかりませんでした。
                </TableCell>
              </TableRow>
            ) : (
              filteredHorses.map((horse) => (
                <TableRow
                  key={horse.id}
                  hover
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell>
                    <RouterLink 
                      to={`/horses/${horse.id}`}
                      style={{ textDecoration: 'none', color: 'inherit' }}
                    >
                      {horse.name}
                    </RouterLink>
                  </TableCell>
                  <TableCell>{Array.isArray(horse.sex) ? horse.sex[0] : horse.sex}</TableCell>
                  <TableCell>{Array.isArray(horse.age) ? horse.age[0] : horse.age}</TableCell>
                  <TableCell>{horse.sire || '-'}</TableCell>
                  <TableCell>{horse.dam || '-'}</TableCell>
                  <TableCell>{horse.damsire || '-'}</TableCell>
                  <TableCell>
                    {horse.sold_price ? 
                      `¥${new Intl.NumberFormat('ja-JP').format(horse.sold_price)}` : 
                      '-'}
                  </TableCell>
                  <TableCell>
                    {horse.auction_date ? 
                      new Date(horse.auction_date).toLocaleDateString('ja-JP') : 
                      '-'}
                  </TableCell>
                  <TableCell>
                    <Button 
                      variant="outlined" 
                      size="small"
                      component={RouterLink}
                      to={`/horses/${horse.id}`}
                    >
                      詳細
                    </Button>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {totalPages > 1 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
            disabled={loading}
            sx={{ mt: 2 }}
          />
        </Box>
      )}
    </Box>
  );
};

export default HorseList;