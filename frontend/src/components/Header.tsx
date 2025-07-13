import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import { Pets, Dashboard, CloudDownload } from '@mui/icons-material';

const Header: React.FC = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Pets sx={{ mr: 2 }} />
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          サラブレッドオークション データベース
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            startIcon={<Dashboard />}
          >
            ダッシュボード
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/horses"
            startIcon={<Pets />}
          >
            馬一覧
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/scraping"
            startIcon={<CloudDownload />}
          >
            スクレイピング
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header; 