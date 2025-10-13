import React from 'react';
import { Typography, Card, CardHeader, CardContent, Box } from '@mui/material';
import { formatManYen } from '../../../../src/utils/format';

export interface PrizeCardProps {
  horse: {
    total_prize_latest?: number | null;
  };
  latestHistory: {
    total_prize_start?: number | null;
  };
}

const PrizeCard: React.FC<PrizeCardProps> = ({ horse, latestHistory }) => {
  if ((latestHistory?.total_prize_start === undefined || latestHistory?.total_prize_start === null) && 
      (horse?.total_prize_latest === undefined || horse?.total_prize_latest === null)) {
    return null;
  }

  const startPrize = Number(latestHistory?.total_prize_start ?? 0);
  const latestPrize = Number(horse?.total_prize_latest ?? 0);
  const diff = latestPrize - startPrize;
  const diffFormatted = diff > 0 ? `+${formatManYen(diff)}` : formatManYen(diff);

  return (
    <Card className="mb-6">
      <CardHeader 
        sx={{
          padding: 0,
          margin: 0,
          '& .MuiCardHeader-content': {
            padding: 0,
            margin: 0
          }
        }}
      >
        <Typography variant="h6" component="h3" sx={{ fontWeight: 'bold', fontSize: '1.25rem', mb: 1 }}>
          賞金情報
        </Typography>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-center">
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {formatManYen(startPrize)}
            </div>
            <div className="text-xs text-gray-600">落札時</div>
          </div>
          <div>
            <div className="text-lg font-semibold text-gray-900">
              {formatManYen(latestPrize)}
            </div>
            <div className="text-xs text-gray-600">現在</div>
          </div>
        </div>
        <div className="border-t pt-4">
          <div className="text-center">
            <div 
              className={`text-xl font-bold ${
                diff > 0 
                  ? 'text-green-600' 
                  : diff < 0 
                    ? 'text-red-600' 
                    : 'text-gray-600'
              }`}
            > 
              {diff === 0 ? '0万円' : diffFormatted}
              {diff !== 0 && (
                <span className="text-sm ml-1">
                  ({diff > 0 ? '増加' : '減少'})
                </span>
              )}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default PrizeCard;
