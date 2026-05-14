'use client';

import { Suspense, useCallback, useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Header } from '@/components/Header';
import { getApiBase } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

type SessionRow = { session_date: string; horse_count: number; source: string };
type Suggestion = { session_date: string; label: string; source: string };

type HorseRow = {
  id: number;
  name: string;
  sex?: string | null;
  age?: string | number | null;
  sire?: string | null;
  dam?: string | null;
  dam_sire?: string | null;
  weight?: number | null;
  total_prize_start?: number | null;
  sold_price_latest?: number | null;
  predicted_price_min: number;
  predicted_price_max: number;
  predicted_price_range_label: string;
  detail_url?: string | null;
  jbis_url?: string | null;
  data_as_of?: string | null;
};

function formatYen(n: number): string {
  if (!n) return '—';
  return new Intl.NumberFormat('ja-JP').format(n) + '円';
}

function AuctionDayContent() {
  const searchParams = useSearchParams();
  const initialDate = searchParams.get('date') || '';

  const [sessions, setSessions] = useState<SessionRow[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [selectedDate, setSelectedDate] = useState(initialDate);
  const [horses, setHorses] = useState<HorseRow[]>([]);
  const [meta, setMeta] = useState<{ total: number; data_as_of?: string | null } | null>(null);
  const [loadingSessions, setLoadingSessions] = useState(true);
  const [loadingHorses, setLoadingHorses] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiBase = useMemo(() => getApiBase(), []);

  useEffect(() => {
    const load = async () => {
      setLoadingSessions(true);
      setError(null);
      try {
        const res = await fetch(`${apiBase}/api/auction-day/sessions?limit=40`);
        if (!res.ok) throw new Error('セッション一覧の取得に失敗しました');
        const data = await res.json();
        setSessions(data.sessions || []);
        setSuggestions(data.upcoming_suggestions || []);
        const dates: string[] = (data.sessions || []).map((s: SessionRow) => s.session_date);
        const sug = (data.upcoming_suggestions || []) as Suggestion[];
        const first = dates[0] || (sug[0] && sug[0].session_date) || '';
        setSelectedDate((prev) => prev || first);
      } catch (e) {
        setError(String((e as Error)?.message || e));
      } finally {
        setLoadingSessions(false);
      }
    };
    load();
  }, [apiBase]);

  const fetchHorses = useCallback(
    async (date: string) => {
      if (!date) return;
      setLoadingHorses(true);
      setError(null);
      try {
        const res = await fetch(
          `${apiBase}/api/auction-day/sessions/${encodeURIComponent(date)}/horses?skip=0&limit=200`
        );
        if (!res.ok) throw new Error('馬一覧の取得に失敗しました');
        const data = await res.json();
        setHorses(data.horses || []);
        setMeta(data.metadata || null);
      } catch (e) {
        setError(String((e as Error)?.message || e));
        setHorses([]);
        setMeta(null);
      } finally {
        setLoadingHorses(false);
      }
    },
    [apiBase]
  );

  useEffect(() => {
    if (selectedDate) {
      void fetchHorses(selectedDate);
    }
  }, [selectedDate, fetchHorses]);

  useEffect(() => {
    const d = searchParams.get('date');
    if (d) setSelectedDate(d);
  }, [searchParams]);

  const dateOptions = useMemo(() => {
    const map = new Map<string, string>();
    sessions.forEach((s) => map.set(s.session_date, `${s.session_date}（${s.horse_count}頭）`));
    suggestions.forEach((s) => {
      if (!map.has(s.session_date)) map.set(s.session_date, `${s.session_date}（${s.label}）`);
    });
    return Array.from(map.entries());
  }, [sessions, suggestions]);

  return (
    <>
      <Header pageTitle="サラオクDB｜オークション当日モード" />
      <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>開催日</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2 items-center">
            {loadingSessions && <span className="text-sm text-gray-500">読み込み中…</span>}
            {!loadingSessions &&
              dateOptions.map(([value, label]) => (
                <Button
                  key={value}
                  type="button"
                  variant={selectedDate === value ? 'default' : 'outline'}
                  className={
                    selectedDate === value
                      ? 'rounded-md bg-black text-white hover:bg-gray-800'
                      : 'rounded-md bg-white border border-black text-black hover:bg-gray-100'
                  }
                  onClick={() => setSelectedDate(value)}
                >
                  {label}
                </Button>
              ))}
            {selectedDate && (
              <Link href={`/auction-day?date=${encodeURIComponent(selectedDate)}`} className="text-xs text-gray-500 ml-2">
                この日付のURLをコピー
              </Link>
            )}
          </CardContent>
        </Card>

        {error && (
          <div className="rounded-md border border-red-200 bg-red-50 text-red-800 px-4 py-2 text-sm">{error}</div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex flex-wrap justify-between gap-2">
              <span>出品馬と予想レンジ</span>
              {meta && (
                <span className="text-sm font-normal text-gray-500">
                  {meta.total}頭 / 鮮度: {meta.data_as_of || '—'}
                </span>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingHorses && <p className="text-sm text-gray-500">馬データを読み込み中…</p>}
            {!loadingHorses && horses.length === 0 && selectedDate && (
              <p className="text-sm text-gray-500">この開催日の馬がまだありません。</p>
            )}
            {!loadingHorses && horses.length > 0 && (
              <div className="overflow-x-auto">
                <table className="min-w-full text-sm border-collapse">
                  <thead>
                    <tr className="border-b text-left text-gray-600">
                      <th className="py-2 pr-3">馬名</th>
                      <th className="py-2 pr-3">性齢</th>
                      <th className="py-2 pr-3">父</th>
                      <th className="py-2 pr-3">体重</th>
                      <th className="py-2 pr-3">出品時賞金(万)</th>
                      <th className="py-2 pr-3">予想レンジ</th>
                      <th className="py-2 pr-3">予想（円）</th>
                      <th className="py-2 pr-3">落札</th>
                      <th className="py-2 pr-3">リンク</th>
                    </tr>
                  </thead>
                  <tbody>
                    {horses.map((h) => (
                      <tr key={h.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-2 pr-3 whitespace-nowrap">
                          <Link href={`/horses/${h.id}`} className="text-blue-700 underline">
                            {h.name}
                          </Link>
                        </td>
                        <td className="py-2 pr-3 whitespace-nowrap">
                          {h.sex}
                          {h.age != null && h.age !== '' ? `${h.age}歳` : ''}
                        </td>
                        <td className="py-2 pr-3 max-w-[140px] truncate" title={h.sire || ''}>
                          {h.sire || '—'}
                        </td>
                        <td className="py-2 pr-3">{h.weight ?? '—'}</td>
                        <td className="py-2 pr-3">
                          {h.total_prize_start != null
                            ? new Intl.NumberFormat('ja-JP', { maximumFractionDigits: 1 }).format(h.total_prize_start)
                            : '—'}
                        </td>
                        <td className="py-2 pr-3 whitespace-nowrap">{h.predicted_price_range_label || '—'}</td>
                        <td className="py-2 pr-3 text-xs whitespace-nowrap">
                          {formatYen(h.predicted_price_min)} 〜 {formatYen(h.predicted_price_max)}
                        </td>
                        <td className="py-2 pr-3 text-xs whitespace-nowrap">
                          {h.sold_price_latest != null ? formatYen(Math.round(h.sold_price_latest)) : '—'}
                        </td>
                        <td className="py-2 pr-3 flex flex-col gap-1">
                          {h.detail_url && (
                            <a href={h.detail_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                              楽天
                            </a>
                          )}
                          {h.jbis_url && (
                            <a href={h.jbis_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">
                              JBIS
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

export default function AuctionDayPage() {
  return (
    <Suspense
      fallback={
        <div>
          <Header pageTitle="サラオクDB｜オークション当日モード" />
          <p className="px-4 py-8 text-sm text-gray-500">読み込み中…</p>
        </div>
      }
    >
      <AuctionDayContent />
    </Suspense>
  );
}
