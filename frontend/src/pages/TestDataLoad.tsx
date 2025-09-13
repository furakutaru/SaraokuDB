import React, { useState, useEffect } from 'react';
import { Box, Typography, Button } from '@mui/material';

const TestDataLoad: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      // 直接JSONファイルを読み込む
      const response = await fetch('/data/horses_history.json');
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const jsonData = await response.json();
      setData(jsonData);
    } catch (err) {
      console.error('Error loading data:', err);
      setError('データの読み込み中にエラーが発生しました');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box p={4}>
      <Typography variant="h4" gutterBottom>データ読み込みテスト</Typography>
      <Button 
        variant="contained" 
        color="primary" 
        onClick={loadData}
        disabled={loading}
        sx={{ mb: 2 }}
      >
        {loading ? '読み込み中...' : 'データを読み込む'}
      </Button>

      {error && (
        <Typography color="error" paragraph>
          エラー: {error}
        </Typography>
      )}

      {data && (
        <Box>
          <Typography variant="h6" gutterBottom>データ構造:</Typography>
          <pre style={{ 
            backgroundColor: '#f5f5f5', 
            padding: '16px', 
            borderRadius: '4px',
            maxHeight: '400px',
            overflow: 'auto'
          }}>
            {JSON.stringify(data, null, 2)}
          </pre>
          
          <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>馬の数: {data.horses?.length || 0}</Typography>
          
          {data.horses && data.horses.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle1">最初の馬の情報:</Typography>
              <pre style={{ 
                backgroundColor: '#f0f0f0', 
                padding: '12px', 
                borderRadius: '4px',
                maxHeight: '300px',
                overflow: 'auto'
              }}>
                {JSON.stringify(data.horses[0], null, 2)}
              </pre>
            </Box>
          )}
        </Box>
      )}
    </Box>
  );
};

export default TestDataLoad;
