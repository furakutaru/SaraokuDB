import React from 'react';
import { Typography, Button, Box } from '@mui/material';
import Link from 'next/link';

const Header: React.FC = () => {
  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <Link href="/" passHref>
            <Typography 
              variant="h6" 
              component="a"
              className="text-xl font-bold text-gray-900 hover:text-gray-700 cursor-pointer"
            >
              サラオクDB
            </Typography>
          </Link>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Button
              component={Link}
              href="/analysis"
              variant="text"
              className="text-gray-700 hover:bg-gray-100"
            >
              解析
            </Button>
            <Button
              component={Link}
              href="/recent"
              variant="contained"
              color="primary"
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              直近の追加
            </Button>
          </Box>
        </div>
      </div>
    </header>
  );
};

export default Header; 