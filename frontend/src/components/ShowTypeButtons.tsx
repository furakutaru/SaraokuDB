'use client';

import React from 'react';
import { Button } from './ui/button';

type ShowType = 'all' | 'sold' | 'unsold' | 'roi' | 'value';

interface ShowTypeButtonsProps {
  showType: ShowType;
  onChange: (value: ShowType) => void;
}

export default function ShowTypeButtons({ showType, onChange }: ShowTypeButtonsProps) {
  return (
    <div className="flex gap-4 mb-6">
      <Button onClick={() => onChange('all')} variant="default" className={showType==='all'?"bg-blue-600 text-white":"bg-blue-400 text-white"}>全馬</Button>
      <Button onClick={() => onChange('roi')} variant="default" className={showType==='roi'?"bg-green-600 text-white":"bg-green-400 text-white"}>ROIランキング</Button>
      <Button onClick={() => onChange('value')} variant="default" className={showType==='value'?"bg-orange-600 text-white":"bg-orange-400 text-white"}>妙味馬</Button>
    </div>
  );
}
