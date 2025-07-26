import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  Pagination,
  Alert,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  TablePagination,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import axios from 'axios';
import { Horse } from '../types/horse';

// Use the imported Horse type from types/horse

const calcROI = (prize: number, price: number) => {
  if (!price || price === 0) return '-';
  return (price / prize).toFixed(2);
};

export default function Dashboard() {
  const [horses, setHorses] = useState<Horse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const rowsPerPage = 10;
  const [showType, setShowType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDate, setSelectedDate] = useState<string>('');
  const navigate = useNavigate();

  // Initialize missing data state
  const [missingData, setMissingData] = useState({
    horsesWithMissingData: [] as number[],
    totalHorses: 0,
    missingFields: {
      name: 0,
      sex: 0,
      age: 0,
      sire: 0,
      dam: 0,
      dam_sire: 0,
      weight: 0,
      total_prize_latest: 0,
      comment: 0
    }
  });

  // Handle show type change
  const handleShowTypeChange = (event: SelectChangeEvent) => {
    setShowType(event.target.value);
    setPage(1);
  };

  // オークション開催日の一覧を取得
  const auctionDates = useMemo(() => 
    [...new Set(horses.map(horse => horse.auction_date))].sort().reverse(),
    [horses]
  );

  // 馬データを取得
  useEffect(() => {
    const fetchHorses = async () => {
      try {
        const response = await axios.get('/api/horses');
        const horseData = response.data.map((horse: any) => ({
          ...horse,
          // Ensure weight is either number or undefined to match the Horse type
          weight: horse.weight || undefined
        }));
        setHorses(horseData);
        setLoading(false);
      } catch (err) {
        setError('データの取得に失敗しました');
        setLoading(false);
        console.error('Error fetching horses:', err);
      }
    };

    fetchHorses();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box p={3}>
        <Alert severity="error">{error}</Alert>
      </Box>
    );
  }

  // フィルタリングされた馬のリスト
  const filteredHorses = useMemo(() => {
    let result = [...horses];
    
    // 検索キーワードでフィルタリング
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      result = result.filter(horse => 
        horse.name?.toLowerCase().includes(term) ||
        horse.sire?.toLowerCase().includes(term) ||
        horse.dam?.toLowerCase().includes(term) ||
        horse.dam_sire?.toLowerCase().includes(term)
      );
    }
    
    // オークション日でフィルタリング
    if (selectedDate) {
      result = result.filter(horse => horse.auction_date === selectedDate);
    }
    
    return result;
  }, [horses, searchTerm, selectedDate]);

  // ページネーションで表示する馬を選択
  const paginatedHorses = useMemo(() => {
    let result = [...filteredHorses];
    
    // 表示タイプでフィルタリング
    if (showType === 'withMissingData') {
      const missingDataSummary = getMissingDataSummary(filteredHorses);
      result = result.filter(horse => 
        missingDataSummary.horsesWithMissingData.includes(horse.id)

  // 不足データアラートを表示するかどうか
  const showMissingDataAlert = useMemo(() => {
    return missingData?.horsesWithMissingData?.length > 0;
  }, [missingData]);

  // ページネーション
  const totalPages = useMemo(() => {
    return Math.ceil((filteredHorses?.length || 0) / rowsPerPage);
  }, [filteredHorses, rowsPerPage]);

  // 表示する馬のデータをフィルタリング
  const paginatedHorses = useMemo(() => {
    if (!filteredHorses) return [];
    const start = (page - 1) * rowsPerPage;
    const end = start + rowsPerPage;
    return filteredHorses.slice(start, end);
  }, [filteredHorses, page, rowsPerPage]);

  // テーブルの行をレンダリング
  const renderTableRows = () => {
    if (!paginatedHorses || paginatedHorses.length === 0) {
      return (
        <TableRow>
          <TableCell colSpan={10} align="center">
            表示するデータがありません
          </TableCell>
        </TableRow>
      );
    }

    return paginatedHorses.map((horse: Horse) => (
      <TableRow key={horse.id}>
        <TableCell>
          <Link 
            to={`/horses/${horse.id}`} 
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            {horse.name || '-'}
          </Link>
        </TableCell>
        <TableCell>{horse.sex || '-'}</TableCell>
        <TableCell>{horse.age || '-'}</TableCell>
        <TableCell>{horse.sire || '-'}</TableCell>
        <TableCell>{horse.dam || '-'}</TableCell>
        <TableCell>{horse.dam_sire || '-'}</TableCell>
        <TableCell>{horse.weight ? `${horse.weight} kg` : '-'}</TableCell>
        <TableCell>
          {horse.total_prize_latest ? 
            `${new Intl.NumberFormat('ja-JP').format(horse.total_prize_latest)} 万円` : 
            '-'}
        </TableCell>
        <TableCell>
          {horse.auction_date ? new Date(horse.auction_date).toLocaleDateString('ja-JP') : '-'}
        </TableCell>
        <TableCell>
          <Button 
            variant="outlined" 
            size="small"
            onClick={() => navigate(`/horses/${horse.id}/edit`)}
          >
            編集
          </Button>
        </TableCell>
      </TableRow>
    ));
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        ダッシュボード
      </Typography>
      
      {/* 不足データアラート */}
      {showMissingDataAlert && (
        <Box mb={3}>
          <Alert severity="warning">
            {missingData.horsesWithMissingData.length}頭の馬に不足データがあります。詳細は各馬の詳細ページで確認してください。
          </Alert>
        </Box>
      )}

      {/* 検索とフィルター */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 3, gap: 2, flexWrap: 'wrap' }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', flex: 1 }}>
          <TextField
            label="検索"
            variant="outlined"
            size="small"
            value={searchTerm}
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setPage(1);
            }}
            sx={{ minWidth: 200 }}
          />
          <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
            <InputLabel>オークション日</InputLabel>
            <Select
              value={selectedDate}
              onChange={(e) => {
                setSelectedDate(e.target.value as string);
                setPage(1);
              }}
              label="オークション日"
            >
              <MenuItem value="">すべての日付</MenuItem>
              {auctionDates.map(date => (
                <MenuItem key={date} value={date}>
                  {new Date(date).toLocaleDateString('ja-JP')}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl variant="outlined" size="small" sx={{ minWidth: 200 }}>
            <InputLabel>表示</InputLabel>
            <Select
              value={showType}
              onChange={handleShowTypeChange}
              label="表示"
            >
              <MenuItem value="all">すべての馬</MenuItem>
              <MenuItem value="withMissingData">不足データあり</MenuItem>
            </Select>
          </FormControl>
        </Box>
        <Button 
          variant="contained" 
          color="primary"
          onClick={() => navigate('/horses/new')}
          sx={{ minWidth: 120 }}
        >
          新規登録
        </Button>
      </Box>

      {/* テーブル */}
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
              <TableCell>馬体重</TableCell>
              <TableCell>獲得賞金</TableCell>
              <TableCell>オークション日</TableCell>
              <TableCell>アクション</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {renderTableRows()}
          </TableBody>
        </Table>
      </TableContainer>

      {/* ページネーション */}
      {filteredHorses.length > 0 && (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
          <Pagination 
            count={Math.ceil(filteredHorses.length / rowsPerPage)} 
            page={page}
            onChange={(_, value) => setPage(value)}
            color="primary"
            showFirstButton 
            showLastButton
          />
        </Box>
      )}
    </Box>
  );
}

export default Dashboard;
        <Card sx={{ minWidth: 200, flex: 1 }}>
          <CardContent>
            <Typography color="textSecondary">平均賞金</Typography>
            <Typography variant="h5">
              {filteredHorses.length > 0 
                ? (filteredHorses.reduce((sum, h) => sum + (h.total_prize_latest || 0), 0) / filteredHorses.length).toFixed(1) + ' 万円'
                : '-'}
            </Typography>
          </CardContent>
        </Card>
      </Box>
          </Card>
        </div>
        {/* 指標ボタン */}
        <div className="flex gap-4 mb-6">
          <Button onClick={() => setShowType('all')} variant={showType==='all'?'default':'outline'}>全馬</Button>
          <Button onClick={() => setShowType('roi')} variant={showType==='roi'?'default':'outline'}>ROIランキング</Button>
          <Button onClick={() => setShowType('value')} variant={showType==='value'?'default':'outline'}>妙味馬</Button>
        </div>
        {/* DataTable風の表 */}
        <div className="overflow-x-auto bg-white rounded-lg shadow">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">馬名</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">性別</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">年齢</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">父</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">落札価格</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">オークション時賞金</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">現在賞金</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">ROI</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">画像</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">リンク</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {tableHorses.map((horse) => (
                <tr key={horse.id} className="hover:bg-blue-50">
                  <td className="px-3 py-2 font-medium text-gray-900">
                    <Link href={`/horses/${horse.id}`} className="hover:underline text-blue-700">{horse.name}</Link>
                  </td>
                  <td className="px-3 py-2">{horse.sex}</td>
                  <td className="px-3 py-2">{horse.age}</td>
                  <td className="px-3 py-2">{horse.sire}</td>
                  <td className="px-3 py-2">{horse.sold_price}</td>
                  <td className="px-3 py-2">{horse.total_prize_start}</td>
                  <td className="px-3 py-2">{horse.total_prize_latest}</td>
                  <td className="px-3 py-2">{horse.sold_price && horse.total_prize_latest ? (horse.total_prize_latest / horse.sold_price).toFixed(2) : '-'}</td>
                  <td className="px-3 py-2">
                    {horse.primary_image ? (
                      <HorseImage src={horse.primary_image} alt={horse.name} className="w-12 h-12 object-contain rounded bg-gray-100" />
                    ) : (
                      <span className="text-gray-400">No Image</span>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-col gap-1">
                      {horse.jbis_url && (
                        <a href={horse.jbis_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 underline">JBIS</a>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
} 