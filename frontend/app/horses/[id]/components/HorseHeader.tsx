import React from 'react';
import { Typography, Button, Box, CardHeader } from '@mui/material';
import { format } from 'date-fns';
import { ja } from 'date-fns/locale';

interface HorseHeaderProps {
  name: string;
  sex: string | string[];
  age: number | string;
  color?: string;
  birthday?: string;
  jbis_url?: string | string[];
  rakuten_url?: string | string[];
  detail_url?: string | string[];
  auction_url?: string | string[];
  id?: string | number;
}

export const HorseHeader: React.FC<HorseHeaderProps> = ({
  name,
  sex,
  age,
  color,
  birthday,
  jbis_url,
  rakuten_url,
  detail_url,
  auction_url,
  id
}) => {
  // デバッグ用ログ
  console.log('HorseHeader - Debug:', {
    jbis_url,
    rakuten_url,
    detail_url,
    auction_url,
    id,
    all_props: { name, sex, age, color, birthday }
  });

  // URLを正規化するヘルパー関数
  const normalizeUrl = (url: string | string[] | undefined): string => {
    if (!url) return '';
    const urlStr = Array.isArray(url) ? url[0] : url;
    return urlStr.startsWith('http') ? urlStr : `https://${urlStr}`;
  };

  // JBIS URLを構築
  const jbisUrl = normalizeUrl(jbis_url);
  const rakutenUrl = normalizeUrl(rakuten_url || auction_url);
  const detailUrl = normalizeUrl(detail_url);

  return (
    <CardHeader>
      <div className="flex justify-between items-start w-full">
        <div>
          <Typography variant="h5" component="h2" sx={{ fontWeight: 'bold', fontSize: '1.5rem', mb: 1 }}>
            {name}
          </Typography>
          <Typography variant="body2" color="text.secondary" className="mb-2">
            {Array.isArray(sex) ? sex[0] : sex || ''} {age}歳 | {color} | {birthday ? format(new Date(birthday), 'yyyy年M月d日', { locale: ja }) : '生年月日不明'}
          </Typography>
          <div className="flex space-x-2 mt-2">
            {jbisUrl && (
              <a 
                href={jbisUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-3 py-1 bg-blue-600 text-white text-sm font-medium rounded-full hover:bg-blue-700 transition-colors"
              >
                JBIS
              </a>
            )}
            {rakutenUrl && (
              <a 
                href={rakutenUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-3 py-1 bg-red-600 text-white text-sm font-medium rounded-full hover:bg-red-700 transition-colors"
              >
                楽天オークション
              </a>
            )}
            {detailUrl && (
              <a 
                href={detailUrl} 
                target="_blank" 
                rel="noopener noreferrer"
                className="px-3 py-1 bg-green-600 text-white text-sm font-medium rounded-full hover:bg-green-700 transition-colors"
              >
                詳細ページ
              </a>
            )}
          </div>
        </div>
        <Button 
          variant="outlined" 
          size="small"
          onClick={() => window.history.back()}
          className="rounded-md bg-white border border-black text-black hover:bg-gray-100"
        >
          戻る
        </Button>
      </div>
    </CardHeader>
  );
};

export default HorseHeader;
