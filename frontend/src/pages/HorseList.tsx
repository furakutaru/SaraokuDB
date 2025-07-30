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
  Pagination
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import axios from 'axios';

interface HistoryEntry {
  auction_date: string;
  sold_price: number | null;
  total_prize_start: number;
  [key: string]: any;
}

interface Horse {
  id: number;
  name: string;
  sex: string;
  age: string | number;
  primary_image: string;
  history: HistoryEntry[];
  sold_price?: number | null;
  unsold_count?: number;
  disease_tags?: string[] | string;
  detail_url?: string;
  jbis_url?: string;
  comment?: string;
  [key: string]: any;
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
    try {
      setLoading(true);
      const params: any = {
        skip: (page - 1) * 50,
        limit: 50
      };
      
      if (selectedDate) {
        params.auction_date = selectedDate;
      }
      
      const response = await axios.get('/horses/', { params });
      setHorses(response.data);
      setTotalPages(Math.ceil(response.data.length / 50) + 1);
    } catch (err) {
      setError('馬データの取得に失敗しました');
      console.error('Error fetching horses:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAuctionDates = async () => {
    try {
      const response = await axios.get('/auction-dates/');
      setAuctionDates(response.data);
    } catch (err) {
      console.error('Error fetching auction dates:', err);
    }
  };

  const filteredHorses = horses.filter(horse =>
    horse.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

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

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        馬一覧
      </Typography>
      
      <Box sx={{ mb: 3, display: 'flex', gap: 2 }}>
        <TextField
          label="馬名で検索"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          sx={{ minWidth: 300 }}
          placeholder="馬名を入力"
        />
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>開催日</InputLabel>
          <Select
            value={selectedDate}
            label="開催日"
            onChange={(e) => setSelectedDate(e.target.value)}
          >
            <MenuItem value="">全て</MenuItem>
            {auctionDates.map((date) => (
              <MenuItem key={date} value={date}>
                {date}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>画像</TableCell>
              <TableCell>馬名</TableCell>
              <TableCell>性別</TableCell>
              <TableCell>年齢</TableCell>
              <TableCell>落札価格</TableCell>
              <TableCell>疾病タグ</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredHorses.map((horse) => (
              <TableRow key={horse.id} hover>
                <TableCell>
                  {horse.primary_image ? (
                    <img 
                      src={horse.primary_image} 
                      alt={`${horse.name}の画像`}
                      style={{ 
                        width: '60px', 
                        height: '60px', 
                        objectFit: 'cover',
                        borderRadius: '4px'
                      }}
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.style.display = 'none';
                      }}
                    />
                  ) : (
                    <div style={{ 
                      width: '60px', 
                      height: '60px', 
                      backgroundColor: '#f5f5f5',
                      borderRadius: '4px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '12px',
                      color: '#999'
                    }}>
                      画像なし
                    </div>
                  )}
                </TableCell>
                <TableCell>
                  <RouterLink to={`/horses/${horse.id}`} style={{ textDecoration: 'none', color: 'inherit' }}>
                    {horse.name}
                  </RouterLink>
                </TableCell>
                <TableCell>{horse.sex || '-'}</TableCell>
                <TableCell>{horse.age || '-'}</TableCell>
                <TableCell>
                  {horse.history && 
                   horse.history.length > 0 && 
                   horse.history[0]?.sold_price !== null && 
                   horse.history[0]?.sold_price !== undefined && 
                   horse.history[0]?.sold_price > 0
                    ? `¥${horse.history[0].sold_price.toLocaleString()}`
                    : '¥-'}
                </TableCell>
                <TableCell>
                  {horse.disease_tags ? (
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                      {Array.isArray(horse.disease_tags) ? (
                        horse.disease_tags.map((tag, index) => (
                          <span 
                            key={index}
                            style={{
                              backgroundColor: '#ffebee',
                              color: '#c62828',
                              padding: '2px 8px',
                              borderRadius: '12px',
                              fontSize: '0.75rem',
                              whiteSpace: 'nowrap'
                            }}
                          >
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span 
                          style={{
                            backgroundColor: '#ffebee',
                            color: '#c62828',
                            padding: '2px 8px',
                            borderRadius: '12px',
                            fontSize: '0.75rem',
                            whiteSpace: 'nowrap'
                          }}
                        >
                          {horse.disease_tags}
                        </span>
                      )}
                    </div>
                  ) : '-'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
        <Pagination
          count={totalPages}
          page={page}
          onChange={(_, value) => setPage(value)}
          color="primary"
        />
      </Box>
    </Box>
  );
};

export default HorseList; 