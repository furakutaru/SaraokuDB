'use client';

import { useRouter } from 'next/navigation';
import AnalysisContent from '@/components/AnalysisContent';
import { Horse } from '@/types/horse';
import { DataIntegrityAlert } from '@/components/DataIntegrityAlert';
import { Header } from '@/components/Header';

export default function Home() {
  const router = useRouter();

  // 最新の年齢を取得するヘルパー関数
  const getHorseAge = (horse: any) => {
    // 最新の履歴から年齢を取得
    if (Array.isArray(horse.history) && horse.history.length > 0) {
      const latestHistory = horse.history[horse.history.length - 1];
      // 年齢が数値で有効な場合は文字列に変換して返す
      if (typeof latestHistory.age === 'number' && !isNaN(latestHistory.age)) {
        return latestHistory.age.toString();
      }
    }
    // 履歴に年齢がない、または履歴自体がない場合はトップレベルの年齢を確認
    return typeof horse.age === 'number' ? horse.age.toString() : '';
  };

  // ヘッダー部分を残して、コンテンツ部分をAnalysisContentに置き換え
  return (
    <>
      <DataIntegrityAlert />
      <Header pageTitle="サラオクDB｜次回更新: 毎週木・日 24:00" />
      
      <AnalysisContent />
    </>
  );
}
