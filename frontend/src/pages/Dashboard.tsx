import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDataIntegrityCheck, HorseData } from '../hooks/useDataIntegrityCheck';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  TextField,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Pagination,
  CircularProgress,
  Alert,
  Container,
  InputAdornment,
  IconButton,
  Grid,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import SearchIcon from '@mui/icons-material/Search';

const Dashboard = () => {
  const navigate = useNavigate();
  const [horses, setHorses] = useState<HorseData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [page, setPage] = useState<number>(1);
  const rowsPerPage = 10;
  
  // データ整合性チェックフックを使用
  const { data, isLoading: isCheckingData, error: dataError } = useDataIntegrityCheck();
  
  // データが利用可能になったらhorsesステートを更新
  useEffect(() => {
    if (data) {
      setHorses(data);
      setLoading(false);
    }
  }, [data]);
  
  // エラーハンドリング
  useEffect(() => {
    if (dataError) {
      setError(dataError);
      setLoading(false);
    }
  }, [dataError]);


  const fetchHorses = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('http://localhost:8001/horses/');
      if (!response.ok) {
        throw new Error('データの取得に失敗しました');
      }
      const data = await response.json();
      
      // レスポンスからデータを抽出
      let horsesData = [];
      if (data && data.status === 'success' && Array.isArray(data.data)) {
        horsesData = data.data;
      } else if (Array.isArray(data)) {
        horsesData = data;
      } else if (data && Array.isArray(data.horses)) {
        horsesData = data.horses;
      }
      
      setHorses(horsesData);
    } catch (err) {
      setError('馬データの取得中にエラーが発生しました');
      console.error('Error fetching horses:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHorses();
  }, []);

  // フィルタリングされた馬のリスト
  const filteredHorses = useMemo(() => {
    return horses.filter((horse: HorseData) => {
      const searchTermLower = searchTerm.toLowerCase();
      const nameMatch = horse.name?.toLowerCase().includes(searchTermLower) || false;
      const sireMatch = horse.sire?.toLowerCase().includes(searchTermLower) || false;
      const damMatch = horse.dam?.toLowerCase().includes(searchTermLower) || false;
      const damsireMatch = horse.damsire?.toLowerCase().includes(searchTermLower) || false;
      
      const matchesSearch = nameMatch || sireMatch || damMatch || damsireMatch;
      const matchesDate = !selectedDate || horse.auction_date === selectedDate;
      
      return matchesSearch && matchesDate;
    });
  }, [horses, searchTerm, selectedDate]);

  // ページネーションで表示する馬を選択
  const paginatedHorses = useMemo(() => {
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    return filteredHorses.slice(start, end);
  }, [filteredHorses, page, rowsPerPage]);

  // ページネーションの総ページ数
  const totalPages = Math.max(1, Math.ceil(filteredHorses.length / rowsPerPage));

  // ページ変更ハンドラー
  const handlePageChange = (_: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  // 検索ハンドラー
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setPage(1); // 検索時に1ページ目に戻る
  };

  // オークション日選択ハンドラー
  const handleDateChange = (e: any) => {
    setSelectedDate(e.target.value);
    setPage(1); // フィルター変更時に1ページ目に戻る
  };

  // オークション開催日の一覧を取得
  const auctionDates = useMemo(() => {
    const dates = horses
      .map(horse => horse.auction_date)
      .filter((date): date is string => !!date);
    return Array.from(new Set(dates)).sort().reverse();
  }, [horses]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4, textAlign: 'center' }}>
        <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>
        <Button
          variant="contained"
          color="primary"
          startIcon={<RefreshIcon />}
          onClick={fetchHorses}
        >
          再試行
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', sm: 'row' }, justifyContent: 'space-between', alignItems: { xs: 'stretch', sm: 'center' }, gap: 2, mb: 3 }}>
          <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 0 }}>
            馬データ一覧
          </Typography>
          <Button
            variant="contained"
            color="primary"
            startIcon={<RefreshIcon />}
            onClick={fetchHorses}
            sx={{ width: { xs: '100%', sm: 'auto' } }}
          >
            更新
          </Button>
        </Box>
        
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mb: 3 }}>
          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
            <Box sx={{ width: { xs: '100%', md: '50%' } }}>
              <TextField
                fullWidth
                label="検索"
                variant="outlined"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </Box>
            <Box sx={{ width: { xs: '100%', md: '50%' } }}>
              <TextField
                fullWidth
                type="date"
                label="オークション日でフィルタリング"
                variant="outlined"
                value={selectedDate}
                onChange={(e) => setSelectedDate(e.target.value)}
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Box>
          </Box>
        </Box>
      </Box>
        
      <TableContainer component={Paper}>
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
              <TableCell>売主</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedHorses.length > 0 ? (
              paginatedHorses.map((horse) => (
                <TableRow key={horse.id} hover>
                  <TableCell>{horse.name || '-'}</TableCell>
                  <TableCell>{horse.sex || '-'}</TableCell>
                  <TableCell>{horse.age || '-'}</TableCell>
                  <TableCell>{horse.sire || '-'}</TableCell>
                  <TableCell>{horse.dam || '-'}</TableCell>
                  <TableCell>{horse.damsire || '-'}</TableCell>
                  <TableCell>
                    <div>
                      <div>unsold: {String(horse.unsold)}</div>
                      <div>sold_price: {String(horse.sold_price)}</div>
                      <div>history: {horse.history && horse.history.length > 0 ? 
                        JSON.stringify(horse.history.map((h: any) => h.sold_price)) : 'No history'}</div>
                      <div>raw sold_price type: {typeof horse.sold_price}</div>
                      <div>raw sold_price value: {JSON.stringify(horse.sold_price)}</div>
                      {horse.unsold ? '主取り' : (horse.sold_price ? `¥${Number(horse.sold_price).toLocaleString()}` : '-')}
                    </div>
                  </TableCell>
                  <TableCell>
                    {horse.auction_date ? new Date(horse.auction_date).toLocaleDateString('ja-JP') : '-'}
                  </TableCell>
                  <TableCell>{horse.seller || '-'}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <Typography variant="body1" color="textSecondary">
                    該当する馬データがありません
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
      
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3, mb: 4 }}>
        <Pagination
          count={totalPages}
          page={Math.min(page, totalPages)}
          onChange={handlePageChange}
          color="primary"
          showFirstButton
          showLastButton
        />
      </Box>
    </Container>
  );
};

export default Dashboard;
