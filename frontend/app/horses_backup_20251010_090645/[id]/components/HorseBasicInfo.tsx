import React from 'react';
import { Typography, Box } from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';
import ExternalLinks from './ExternalLinks';

interface HorseBasicInfoProps {
  sex: string | string[];
  age: number | string;
  color?: string;
  birthday?: string;
  jbisUrl?: string | string[];
  auctionUrl?: string | string[];
  className?: string;
}

const HorseBasicInfo: React.FC<HorseBasicInfoProps> = ({
  sex,
  age,
  color,
  birthday,
  jbisUrl,
  auctionUrl,
  className = ''
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
      <div className="space-y-2">
        <div className="flex items-center space-x-4">
          <Typography variant="subtitle2" color="textSecondary">
            性別・年齢
          </Typography>
          <Typography variant="body1">
            {formattedSex.label} {age}歳
          </Typography>
        </div>
        
        {color && (
          <div className="flex items-center space-x-4">
            <Typography variant="subtitle2" color="textSecondary">
              毛色
            </Typography>
            <Typography variant="body1">{color}</Typography>
          </div>
        )}
        
        {birthday && (
          <div className="flex items-center space-x-4">
            <Typography variant="subtitle2" color="textSecondary">
              誕生日
            </Typography>
            <Typography variant="body1">
              {format(new Date(birthday), 'yyyy年M月d日', { locale: ja })}
            </Typography>
          </div>
        )}
        
        <ExternalLinks 
          jbisUrl={Array.isArray(jbisUrl) ? jbisUrl[0] : jbisUrl}
          auctionUrl={Array.isArray(auctionUrl) ? auctionUrl[0] : auctionUrl}
          className="mt-3"
        />
      </div>
    </Box>
  );
};

export default HorseBasicInfo;
