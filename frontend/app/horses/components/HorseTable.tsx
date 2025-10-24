'use client';

import React from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper,
  Skeleton,
  Typography,
  Box
} from '@mui/material';
import Link from 'next/link';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import { parseDate } from '../utils/dateUtils';

// 型定義のインポート
import { Horse, Auction } from '../types';

// 価格を表示用にフォーマットする関数
const formatPrice = (price: any): string => {
  if (price === null || price === undefined || price === '') return '-';
  
  // 数値に変換
  const numPrice = Number(price);
  if (isNaN(numPrice)) return '-';
  
  // 0の場合は非表示
  if (numPrice === 0) return '-';
  
  // 100万円単位でフォーマット
  return `¥${(numPrice / 10000).toLocaleString()}万円`;
};

// 性別と年齢を適切に表示するためのヘルパー関数
const formatAge = (sex: string, age: number): string => {
  if (!sex && !age) return '-';
  
  let sexText = '';
  switch(sex) {
    case '牡':
    case '牡馬':
      sexText = '牡';
      break;
    case '牝':
    case '牝馬':
      sexText = '牝';
      break;
    case 'セ':
    case 'セニ':
      sexText = 'セ';
      break;
    default:
      sexText = sex || '';
  }
  
  return `${sexText}${age || ''}`.trim();
};

// 売り主情報を適切に表示するためのヘルパー関数
const formatSeller = (seller: any): string => {
  if (!seller) return '-';
  
  // 文字列の場合はそのまま返す
  if (typeof seller === 'string') {
    // インボイス登録情報を削除
    return seller
      .replace(/\s*\(?:(?!\s*\d{13}\s*\()(?:[^()]|\([^)]*\))*\)/g, '') // 13桁の数字以外のカッコで囲まれた部分を削除
      .replace(/\s*\(\d{13}\)/g, '') // 13桁の数字のカッコを削除
      .trim();
  }
  
  return '-';
};

interface HorseTableProps {
  horses: Horse[];
  loading: boolean;
  onRowClick: (horse: Horse) => void;
}

export const HorseTable: React.FC<HorseTableProps> = ({ 
  horses, 
  loading, 
  onRowClick 
}) => {
  // ローディング中のスケルトン表示
  if (loading) {
    return (
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>馬名</TableCell>
              <TableCell>性・年齢</TableCell>
              <TableCell>父</TableCell>
              <TableCell>母</TableCell>
              <TableCell>母父</TableCell>
              <TableCell>落札価格</TableCell>
              <TableCell>売主</TableCell>
              <TableCell>オークション日</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {[...Array(10)].map((_, index) => (
              <TableRow key={index}>
                {[...Array(8)].map((_, i) => (
                  <TableCell key={i}>
                    <Skeleton variant="text" width="100%" />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    );
  }

  // データが空の場合
  if (horses.length === 0) {
    return (
      <Box 
        display="flex" 
        justifyContent="center" 
        alignItems="center" 
        minHeight="200px"
        p={4}
      >
        <Typography variant="body1" color="textSecondary">
          該当する馬が見つかりませんでした
        </Typography>
      </Box>
    );
  }

  return (
    <TableContainer component={Paper}>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>馬名</TableCell>
            <TableCell>性・年齢</TableCell>
            <TableCell>父</TableCell>
            <TableCell>母</TableCell>
            <TableCell>母父</TableCell>
            <TableCell>落札価格</TableCell>
            <TableCell>売主</TableCell>
            <TableCell>オークション日</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {horses.map((horse) => {
            // 最新のオークション情報を取得
            const latestAuction: Auction | undefined = horse.auctions?.[0];
            
            return (
              <TableRow 
                key={horse.id} 
                hover 
                onClick={() => onRowClick(horse)}
                style={{ cursor: 'pointer' }}
              >
                <TableCell>
                  <Link href={`/horses/${horse.id}`} passHref>
                    <Typography 
                      component="a" 
                      color="primary"
                      sx={{ textDecoration: 'none', '&:hover': { textDecoration: 'underline' } }}
                    >
                      {horse.name || '-'}
                    </Typography>
                  </Link>
                </TableCell>
                <TableCell>{formatAge(horse.sex, horse.age)}</TableCell>
                <TableCell>{horse.sire || '-'}</TableCell>
                <TableCell>{horse.dam || '-'}</TableCell>
                <TableCell>{horse.damsire || '-'}</TableCell>
                <TableCell>
                  {latestAuction?.is_unsold ? (
                    <span style={{ color: 'red' }}>主取り</span>
                  ) : (
                    formatPrice(latestAuction?.sold_price || horse.sold_price)
                  )}
                </TableCell>
                <TableCell>{formatSeller(latestAuction?.seller || horse.seller)}</TableCell>
                <TableCell>
                  {latestAuction?.auction_date 
                    ? format(parseDate(latestAuction.auction_date), 'yyyy/MM/dd', { locale: ja })
                    : horse.auction_date 
                      ? format(parseDate(horse.auction_date), 'yyyy/MM/dd', { locale: ja })
                      : '-'}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default HorseTable;
