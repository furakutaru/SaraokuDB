import React from 'react';
import { Box, Typography, Chip, Stack } from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

interface HorseInfoCardProps {
  sex: string | string[];
  age: number | string;
  className?: string;
}

export const HorseInfoCard: React.FC<HorseInfoCardProps> = ({
  sex,
  age,
  className = '',
}) => {
  // 性別をフォーマット
  const formatSex = (sexValue: string | string[]) => {
    const sexStr = Array.isArray(sexValue) ? sexValue[0] : sexValue;
    switch (sexStr) {
      case '牡':
        return { label: '牡馬', color: 'primary' as const };
      case '牝':
        return { label: '牝馬', color: 'secondary' as const };
      case 'セ':
        return { label: 'せん馬', color: 'success' as const };
      default:
        return { label: sexStr || '不明', color: 'default' as const };
    }
  };

  const formattedSex = formatSex(sex);
  
  return (
    <Box className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
        <div>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            性別・年齢
          </Typography>
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip 
              label={formattedSex.label} 
              color={formattedSex.color} 
              size="small" 
              variant="outlined"
            />
            <Typography variant="body1">
              {age}歳
            </Typography>
          </Stack>
        </div>

      </Stack>
    </Box>
  );
};

export default HorseInfoCard;
