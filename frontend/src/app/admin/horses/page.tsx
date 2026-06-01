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
  const [togglingBroodmare, setTogglingBroodmare] = useState<Record<string, boolean>>({});

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
      // 新馬名: 編集前は空欄（プレースホルダーで現在の馬名を表示）
      name: edits[idStr]?.name ?? '',
      // 旧馬名: former_name未設定なら現在の馬名を自動入力
      former_name: edits[idStr]?.former_name ?? horse.former_name ?? horse.name ?? '',
    };
  };

  const setEditField = (id: string | number, field: keyof EditState, value: string) => {
    const idStr = String(id);
    setEdits(prev => ({ ...prev, [idStr]: { ...prev[idStr], [field]: value } }));
  };

  const handleSave = async (horse: AdminHorse) => {
    const idStr = String(horse.id);
    const edit = getEdit(horse);
    // 新馬名が空欄のまま保存 → 現在の馬名を維持
    const nameToSave = edit.name.trim() || horse.name || '';
    try {
      setSaving(prev => ({ ...prev, [idStr]: true }));
      const API_BASE = getApiBase();
      const response = await fetch(`${API_BASE}/api/horses/${horse.id}`, {
        method: 'PATCH',
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keibabook_url: edit.keibabook_url,
          name: nameToSave,
          former_name: edit.former_name,
        })
      });
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      setMessage({ text: `${nameToSave || '不明'}の情報を保存しました。`, type: 'success' });
      setHorses(prev => prev.map(h =>
        String(h.id) === idStr
          ? { ...h, keibabook_url: edit.keibabook_url, name: nameToSave, former_name: edit.former_name }
          : h
      ));
    } catch (e: any) {
      setMessage({ text: `保存エラー: ${e.message}`, type: 'error' });
    } finally {
      setSaving(prev => ({ ...prev, [idStr]: false }));
      setTimeout(() => setMessage(null), 3000);
    }
  };

  // 繁殖牝馬フラグをトグルして即時保存
  const handleBroodmareToggle = async (horse: AdminHorse, newValue: boolean) => {
    const idStr = String(horse.id);
    try {
      setTogglingBroodmare(prev => ({ ...prev, [idStr]: true }));
      const API_BASE = getApiBase();
      const response = await fetch(`${API_BASE}/api/horses/${horse.id}`, {
        method: 'PATCH',
        headers: { 'Accept': 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_broodmare: newValue })
      });
      if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
      setHorses(prev => prev.map(h =>
        String(h.id) === idStr ? { ...h, is_broodmare: newValue } : h
      ));
      setMessage({
        text: `${horse.name || '不明'}: 繁殖牝馬フラグを${newValue ? 'ON' : 'OFF'}にしました。`,
        type: 'success'
      });
      setTimeout(() => setMessage(null), 3000);
    } catch (e: any) {
      setMessage({ text: `繁殖牝馬フラグ更新エラー: ${e.message}`, type: 'error' });
    } finally {
      setTogglingBroodmare(prev => ({ ...prev, [idStr]: false }));
    }
  };

  const handleCopy = (text: string, id: string | number) => {
    navigator.clipboard.writeText(text);
    setCopied(String(id));
    setTimeout(() => setCopied(null), 2000);
  };

  const needsCheckHorses = useMemo(() => {
    const threeMonthsAgo = new Date();
    threeMonthsAgo.setMonth(threeMonthsAgo.getMonth() - 3);

    return horses
      .map(h => {
        const soldPrice = Number(h.sold_price || 0);
        const prizeLatest = Number(h.total_prize_latest || 0);

        const auctionDate = h.auction_date ? new Date(h.auction_date) : null;
        // オークション日が3ヶ月以上前 -> 賞金更新対象期間に入っている
        const isOldEnoughForUpdate = auctionDate ? auctionDate <= threeMonthsAgo : true;

        // 名前未決定: 「の数字2桁以上」で終わる仮称馬（例: ベラジオの23）
        const isNamePending = h.name ? /の\d{2,}$/.test(h.name) : false;

        // 捕捉不全: 3ヶ月以上前のオークション馬で、落札価格があるのに賞金0かつURL未設定
        // ※ URL設定済みでprize=0は更新スクリプトの問題であり管理画面では対処不可のため除外
        // ※ 直近3ヶ月以内の馬は除外（まだ更新タイミングでないため）
        const isUpdateMissed =
          soldPrice > 0 &&
          prizeLatest === 0 &&
          !h.keibabook_url &&
          isOldEnoughForUpdate;

        return { horse: h, isNamePending, isUpdateMissed };
      })
      .filter(({ horse, isNamePending, isUpdateMissed }) => !horse.is_broodmare && (isNamePending || isUpdateMissed))
      .sort((a, b) => {
        // 名前未決定を優先表示
        if (a.isNamePending && !b.isNamePending) return -1;
        if (!a.isNamePending && b.isNamePending) return 1;
        // URL未設定を次に
        if (!a.horse.keibabook_url && b.horse.keibabook_url) return -1;
        if (a.horse.keibabook_url && !b.horse.keibabook_url) return 1;
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
              <span className="inline-block bg-orange-100 text-orange-700 text-xs px-1.5 py-0.5 rounded mr-1">名前未決定</span> 仮称（〜の23等）のまま登録されている馬<br />
              <span className="inline-block bg-red-100 text-red-700 text-xs px-1.5 py-0.5 rounded mr-1">捕捉不全</span> 3ヶ月以上前のオークションで落札後も賞金が0のまま（要URL設定）<br />
              正式名称が決まった場合は「新しい馬名」と「旧馬名」を設定してください。
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-8 text-center text-gray-400">読み込み中...</div>
            ) : needsCheckHorses.length === 0 ? (
              <div className="py-8 text-center text-gray-400">要チェックの馬はありません。すべて正常です！</div>
            ) : (
              <div className="space-y-3">
                {needsCheckHorses.map(({ horse, isNamePending, isUpdateMissed }) => {
                  const idStr = String(horse.id);
                  const edit = getEdit(horse);
                  const isSaving = saving[idStr];
                  const isCopied = copied === idStr;

                  return (
                    <div
                      key={horse.id}
                      className="rounded-lg border border-gray-200 bg-white p-4"
                    >
                      {/* 行1: 馬名情報 + バッジ */}
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mb-3">
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
                        {/* フラグバッジ */}
                        {isNamePending && (
                          <span className="bg-orange-100 text-orange-700 text-xs font-medium px-2 py-0.5 rounded">
                            名前未決定
                          </span>
                        )}
                        {isUpdateMissed && (
                          <span className="bg-red-100 text-red-700 text-xs font-medium px-2 py-0.5 rounded">
                            捕捉不全
                          </span>
                        )}
                        <span className="text-sm text-gray-400">|</span>
                        <span className="text-sm text-gray-500">父: {horse.sire || '-'}</span>
                        <span className="text-sm text-gray-500">母: {horse.dam || '-'}</span>
                        {horse.auction_date && (
                          <span className="text-xs text-gray-400">
                            オークション: {horse.auction_date}
                          </span>
                        )}
                      </div>

                      {/* 行2: 新しい馬名 + 旧馬名 */}
                      <div className="grid grid-cols-2 gap-3 mb-3">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">
                            新しい馬名
                            <span className="text-gray-400 font-normal ml-1">（変更ない場合は空欄のまま）</span>
                          </label>
                          <input
                            type="text"
                            value={edit.name}
                            onChange={(e) => setEditField(horse.id, 'name', e.target.value)}
                            placeholder={horse.name || '例: ベラジオプライド'}
                            className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">旧馬名（オークション出品時）</label>
                          <input
                            type="text"
                            value={edit.former_name}
                            onChange={(e) => setEditField(horse.id, 'former_name', e.target.value)}
                            placeholder="旧馬名を入力"
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

                      {/* 行4: 繁殖牝馬フラグ */}
                      <div className="mt-3 pt-3 border-t border-gray-100 flex items-center gap-3">
                        <label className="flex items-center gap-2 cursor-pointer select-none">
                          <input
                            type="checkbox"
                            checked={!!horse.is_broodmare}
                            disabled={togglingBroodmare[idStr]}
                            onChange={(e) => handleBroodmareToggle(horse, e.target.checked)}
                            className="w-4 h-4 rounded border-gray-300 text-pink-600 focus:ring-pink-500 cursor-pointer"
                          />
                          <span className="text-sm text-gray-700">
                            繁殖牝馬
                            {horse.is_broodmare && (
                              <span className="ml-1.5 bg-pink-100 text-pink-700 text-xs px-1.5 py-0.5 rounded font-medium">ON</span>
                            )}
                          </span>
                        </label>
                        {togglingBroodmare[idStr] && (
                          <span className="text-xs text-gray-400">更新中...</span>
                        )}
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
