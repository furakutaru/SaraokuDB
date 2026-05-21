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
  const [edits, setEdits] = useState<Record<string, EditState>>({});
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const API_BASE = getApiBase();
      const url = `${API_BASE}/api/horses?skip=0&limit=5000`;

      const response = await fetch(url, {
        method: 'GET',
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

  // 編集値の初期化（初回アクセス時）
  const getEdit = (horse: AdminHorse): EditState => {
    const idStr = String(horse.id);
    if (edits[idStr]) return edits[idStr];
    return {
      keibabook_url: horse.keibabook_url || '',
      name: horse.name || '',
      former_name: horse.former_name || '',
    };
  };

  const setEditField = (id: string | number, field: keyof EditState, value: string) => {
    const idStr = String(id);
    setEdits(prev => ({
      ...prev,
      [idStr]: { ...getEdit(horses.find(h => String(h.id) === idStr)!), ...prev[idStr], [field]: value }
    }));
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

      const displayName = edit.name || horse.name || '不明';
      setMessage({ text: `${displayName}の情報を保存しました。`, type: 'success' });

      // ローカルstateを更新
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

  // 要チェック馬：ROI <= 0 または名前が未決定っぽい
  const needsCheckHorses = useMemo(() => {
    return horses.filter(h => {
      const soldPrice = Number(h.sold_price || 0);
      const prizeLatest = Number(h.total_prize_latest || 0);
      const prizeStart = Number(h.total_prize_start || 0);

      let roi = 0;
      if (soldPrice > 0) roi = ((prizeLatest - prizeStart) / soldPrice) * 100;

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

      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {message && (
          <div className={`mb-4 p-4 rounded-md border ${message.type === 'success' ? 'bg-green-50 text-green-800 border-green-200' : 'bg-red-50 text-red-800 border-red-200'}`}>
            {message.text}
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle>要チェック馬リスト（{needsCheckHorses.length}件）</CardTitle>
            <p className="text-sm text-gray-500">
              ROIが0以下の馬、または名前が未決定・短すぎる馬（〜の23等）が対象です。<br />
              正式名称が決まった場合は「新しい馬名」欄に入力してください。オークション出品時の名前は「旧馬名」として自動保持され、
              一覧では <strong>新名前（旧名前）</strong> の形式で表示されます。
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-8 text-center text-gray-400">読み込み中...</div>
            ) : needsCheckHorses.length === 0 ? (
              <div className="py-8 text-center text-gray-400">要チェックの馬はありません。すべて正常です！</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 text-sm">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">現在の馬名</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">新しい馬名</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">旧馬名（自動保持）</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">父</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">母</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">競馬ブックURL</th>
                      <th className="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase whitespace-nowrap">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-100">
                    {needsCheckHorses.map((horse) => {
                      const idStr = String(horse.id);
                      const edit = getEdit(horse);
                      const isSaving = saving[idStr];
                      const isCopied = copied === idStr;

                      return (
                        <tr key={horse.id} className={!horse.keibabook_url ? 'bg-yellow-50' : ''}>
                          {/* 現在の馬名 + コピーボタン */}
                          <td className="px-4 py-3 whitespace-nowrap font-medium text-gray-900">
                            <div className="flex items-center gap-2">
                              <span>{horse.name || '不明'}</span>
                              {horse.former_name && (
                                <span className="text-xs text-gray-400">（{horse.former_name}）</span>
                              )}
                              {horse.name && (
                                <button
                                  onClick={() => handleCopy(horse.name || '', idStr)}
                                  className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-2 py-0.5 rounded border transition-colors"
                                  title="馬名をコピー"
                                >
                                  {isCopied ? '✓ 済' : 'コピー'}
                                </button>
                              )}
                            </div>
                          </td>

                          {/* 新しい馬名入力 */}
                          <td className="px-4 py-3">
                            <input
                              type="text"
                              value={edit.name}
                              onChange={(e) => setEditField(horse.id, 'name', e.target.value)}
                              placeholder="例: ベラジオプライド"
                              className="w-36 px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </td>

                          {/* 旧馬名入力（自動でセットされるが手動変更も可） */}
                          <td className="px-4 py-3">
                            <input
                              type="text"
                              value={edit.former_name}
                              onChange={(e) => setEditField(horse.id, 'former_name', e.target.value)}
                              placeholder="例: ベラジオの23"
                              className="w-36 px-2 py-1.5 border border-gray-300 rounded-md text-sm text-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                            />
                          </td>

                          <td className="px-4 py-3 whitespace-nowrap text-gray-500">{horse.sire || '-'}</td>
                          <td className="px-4 py-3 whitespace-nowrap text-gray-500">{horse.dam || '-'}</td>

                          {/* 競馬ブックURL */}
                          <td className="px-4 py-3">
                            <div className="flex flex-col gap-1">
                              <input
                                type="text"
                                value={edit.keibabook_url}
                                onChange={(e) => setEditField(horse.id, 'keibabook_url', e.target.value)}
                                placeholder="https://p.keibabook.co.jp/db/uma/..."
                                className="w-64 px-2 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                              />
                              {edit.keibabook_url && (
                                <a href={edit.keibabook_url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:underline">
                                  リンクを開く →
                                </a>
                              )}
                            </div>
                          </td>

                          {/* 保存ボタン */}
                          <td className="px-4 py-3 text-center whitespace-nowrap">
                            <Button
                              onClick={() => handleSave(horse)}
                              disabled={isSaving}
                              size="sm"
                              className="bg-blue-600 hover:bg-blue-700 text-white"
                            >
                              {isSaving ? '保存中...' : '保存'}
                            </Button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
