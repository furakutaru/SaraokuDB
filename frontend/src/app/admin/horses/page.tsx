'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getApiBase } from '@/lib/utils';
import { Header } from '@/components/Header';
import { Horse } from '@/types/horse';

interface AdminHorse extends Horse {
  keibabook_url?: string;
  former_name?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  sold_price?: number | null;
}

interface EditState {
  keibabook_url: string;
  name: string;
  former_name: string;
}

export default function AdminHorsesPage() {
  const [horses, setHorses] = useState<AdminHorse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [edits, setEdits] = useState<Record<string, Partial<EditState>>>({});
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const API_BASE = getApiBase();
      const response = await fetch(`${API_BASE}/api/horses?skip=0&limit=5000`, {
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' }
      });
      if (!response.ok) throw new Error('データの取得に失敗しました');
      const payload = await response.json();
      setHorses(payload?.horses || []);
    } catch (e: any) {
      setMessage({ text: `データ取得エラー: ${e.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  const getEdit = (horse: AdminHorse): EditState => {
    const idStr = String(horse.id);
    return {
      keibabook_url: edits[idStr]?.keibabook_url ?? horse.keibabook_url ?? '',
      name: edits[idStr]?.name ?? horse.name ?? '',
      former_name: edits[idStr]?.former_name ?? horse.former_name ?? '',
    };
  };

  const setEditField = (id: string | number, field: keyof EditState, value: string) => {
    const idStr = String(id);
    setEdits(prev => ({ ...prev, [idStr]: { ...prev[idStr], [field]: value } }));
  };

  const handleSave = async (horse: AdminHorse) => {
    const idStr = String(horse.id);
    const edit = getEdit(horse);
    try {
      setSaving(prev => ({ ...prev, [idStr]: true }));
      const API_BASE = getApiBase();
      const response = await fetch(`${API_BASE}/api/horses/${horse.id}`, {
        method: 'PATCH',
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keibabook_url: edit.keibabook_url,
          name: edit.name,
          former_name: edit.former_name,
        })
      });
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      setMessage({ text: `${edit.name || horse.name || '不明'}の情報を保存しました。`, type: 'success' });
      setHorses(prev => prev.map(h =>
        String(h.id) === idStr
          ? { ...h, keibabook_url: edit.keibabook_url, name: edit.name, former_name: edit.former_name }
          : h
      ));
    } catch (e: any) {
      setMessage({ text: `保存エラー: ${e.message}`, type: 'error' });
    } finally {
      setSaving(prev => ({ ...prev, [idStr]: false }));
      setTimeout(() => setMessage(null), 3000);
    }
  };

  const handleCopy = (text: string, id: string | number) => {
    navigator.clipboard.writeText(text);
    setCopied(String(id));
    setTimeout(() => setCopied(null), 2000);
  };

  const needsCheckHorses = useMemo(() => {
    return horses.filter(h => {
      const soldPrice = Number(h.sold_price || 0);
      const prizeLatest = Number(h.total_prize_latest || 0);
      const prizeStart = Number(h.total_prize_start || 0);
      const roi = soldPrice > 0 ? ((prizeLatest - prizeStart) / soldPrice) * 100 : 0;
      const isRoiNegative = soldPrice > 0 && roi <= 0 && prizeLatest === 0;
      const isNameSuspicious = h.name ? /の\d{2}$/.test(h.name) || h.name.length <= 2 : true;
      return isRoiNegative || isNameSuspicious;
    }).sort((a, b) => {
      if (!a.keibabook_url && b.keibabook_url) return -1;
      if (a.keibabook_url && !b.keibabook_url) return 1;
      return 0;
    });
  }, [horses]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header pageTitle="手動同定管理画面" />

      <main className="max-w-4xl mx-auto py-8 px-4">
        {message && (
          <div className={`mb-4 p-3 rounded-md border text-sm ${message.type === 'success' ? 'bg-green-50 text-green-800 border-green-200' : 'bg-red-50 text-red-800 border-red-200'}`}>
            {message.text}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>要チェック馬リスト（{needsCheckHorses.length}件）</CardTitle>
            <p className="text-sm text-gray-500">
              ROIが0以下の馬、または名前が未決定・短すぎる馬（〜の23等）が対象です。<br />
              正式名称が決まった場合は「新しい馬名」と「旧馬名」を設定してください。一覧では <strong>新名前（旧名前）</strong> の形式で表示されます。
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-8 text-center text-gray-400">読み込み中...</div>
            ) : needsCheckHorses.length === 0 ? (
              <div className="py-8 text-center text-gray-400">要チェックの馬はありません。すべて正常です！</div>
            ) : (
              <div className="space-y-3">
                {needsCheckHorses.map((horse) => {
                  const idStr = String(horse.id);
                  const edit = getEdit(horse);
                  const isSaving = saving[idStr];
                  const isCopied = copied === idStr;
                  const hasNoUrl = !horse.keibabook_url;

                  return (
                    <div
                      key={horse.id}
                      className={`rounded-lg border p-4 ${hasNoUrl ? 'border-yellow-300 bg-yellow-50' : 'border-gray-200 bg-white'}`}
                    >
                      {/* 行1: 馬名情報 + 父・母 */}
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-3">
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-gray-900">{horse.name || '不明'}</span>
                          {horse.name && (
                            <button
                              onClick={() => handleCopy(horse.name || '', idStr)}
                              className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-0.5 rounded border transition-colors"
                            >
                              {isCopied ? '✓ 済' : 'コピー'}
                            </button>
                          )}
                        </div>
                        <span className="text-sm text-gray-400">|</span>
                        <span className="text-sm text-gray-500">父: {horse.sire || '-'}</span>
                        <span className="text-sm text-gray-500">母: {horse.dam || '-'}</span>
                      </div>

                      {/* 行2: 新しい馬名 + 旧馬名 */}
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">新しい馬名</label>
                          <input
                            type="text"
                            value={edit.name}
                            onChange={(e) => setEditField(horse.id, 'name', e.target.value)}
                            placeholder="例: ベラジオプライド"
                            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">旧馬名（オークション出品時）</label>
                          <input
                            type="text"
                            value={edit.former_name}
                            onChange={(e) => setEditField(horse.id, 'former_name', e.target.value)}
                            placeholder="例: ベラジオの23"
                            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                      </div>

                      {/* 行3: 競馬ブックURL + 保存ボタン */}
                      <div className="flex gap-2 items-end">
                        <div className="flex-1">
                          <label className="block text-xs text-gray-500 mb-1">競馬ブックURL</label>
                          <input
                            type="text"
                            value={edit.keibabook_url}
                            onChange={(e) => setEditField(horse.id, 'keibabook_url', e.target.value)}
                            placeholder="https://p.keibabook.co.jp/db/uma/..."
                            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                          {edit.keibabook_url && (
                            <a href={edit.keibabook_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline mt-0.5 inline-block">
                              リンクを開く →
                            </a>
                          )}
                        </div>
                        <div className="pb-0.5">
                          <Button
                            onClick={() => handleSave(horse)}
                            disabled={isSaving}
                            size="sm"
                            className="bg-blue-600 hover:bg-blue-700 text-white whitespace-nowrap"
                          >
                            {isSaving ? '保存中...' : '保存'}
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
