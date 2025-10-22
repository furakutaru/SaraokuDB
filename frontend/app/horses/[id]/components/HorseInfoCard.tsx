import React from 'react';
import { Box, Typography, Stack } from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import SexBadge from '../../components/SexBadge';

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
  return (
    <Box className={`bg-white rounded-lg shadow p-4 ${className}`}>
      <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
        <div>
          <Typography variant="subtitle2" color="textSecondary" gutterBottom>
            性別・年齢
          </Typography>
          <div className="flex items-center">
            <SexBadge sex={sex} age={typeof age === 'number' ? age : parseInt(age as string, 10) || null} />
          </div>
        </div>
      </Stack>
    </Box>
  );
};

export default HorseInfoCard;
