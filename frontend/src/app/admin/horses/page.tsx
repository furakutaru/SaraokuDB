'use client';

import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { getApiBase } from '@/lib/utils';
import { Header } from '@/components/Header';
import { Horse } from '@/types/horse';

interface AdminHorse extends Horse {
  keibabook_url?: string;
  total_prize_start?: number;
  total_prize_latest?: number;
  sold_price?: number | null;
}

export default function AdminHorsesPage() {
  const [horses, setHorses] = useState<AdminHorse[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<Record<string, boolean>>({});
  const [editedUrls, setEditedUrls] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const API_BASE = getApiBase();
      const url = `${API_BASE}/api/horses?skip=0&limit=5000`;
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) throw new Error('データの取得に失敗しました');
      const payload = await response.json();
      const horsesData = payload?.horses || [];
      
      setHorses(horsesData);
    } catch (e: any) {
      console.error('データ取得エラー:', e);
      setMessage({ text: `データ取得エラー: ${e.message}`, type: 'error' });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleUrlChange = (id: string | number, value: string) => {
    setEditedUrls(prev => ({ ...prev, [String(id)]: value }));
  };

  const handleSave = async (horse: AdminHorse) => {
    const idStr = String(horse.id);
    const newUrl = editedUrls[idStr] !== undefined ? editedUrls[idStr] : horse.keibabook_url || '';
    
    try {
      setSaving(prev => ({ ...prev, [idStr]: true }));
      const API_BASE = getApiBase();
      
      const response = await fetch(`${API_BASE}/api/horses/${horse.id}`, {
        method: 'PATCH',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keibabook_url: newUrl })
      });

      if (!response.ok) {
        throw new Error(`HTTP Error: ${response.status}`);
      }
      
      setMessage({ text: `${horse.name || '不明'}のURLを保存しました。`, type: 'success' });
      
      // Update local state
      setHorses(prev => prev.map(h => 
        String(h.id) === idStr ? { ...h, keibabook_url: newUrl } : h
      ));
      
    } catch (e: any) {
      console.error('保存エラー:', e);
      setMessage({ text: `保存エラー: ${e.message}`, type: 'error' });
    } finally {
      setSaving(prev => ({ ...prev, [idStr]: false }));
      setTimeout(() => setMessage(null), 3000);
    }
  };

  // 1. ROIが0以下、または名前が「の23」など、またはURLが未登録の馬を抽出
  const needsCheckHorses = useMemo(() => {
    return horses.filter(h => {
      const soldPrice = Number(h.sold_price || 0);
      const prizeLatest = Number(h.total_prize_latest || 0);
      const prizeStart = Number(h.total_prize_start || 0);
      
      let roi = 0;
      if (soldPrice > 0) {
        roi = ((prizeLatest - prizeStart) / soldPrice) * 100;
      }
      
      const isRoiNegative = soldPrice > 0 && roi <= 0 && prizeLatest === 0;
      const isNameSuspicious = h.name ? /の\d{2}$/.test(h.name) || h.name.length <= 2 : true;
      const noUrl = !h.keibabook_url;
      
      return isRoiNegative || isNameSuspicious || noUrl;
    }).sort((a, b) => {
      // 未設定のものを上に
      if (!a.keibabook_url && b.keibabook_url) return -1;
      if (a.keibabook_url && !b.keibabook_url) return 1;
      return 0;
    });
  }, [horses]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header pageTitle="手動同定管理画面 (競馬ブックURL設定)" />
      
      <main className="max-w-6xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {message && (
          <div className={`mb-4 p-4 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-800 border-green-200' : 'bg-red-50 text-red-800 border-red-200'} border`}>
            {message.text}
          </div>
        )}
        
        <Card>
          <CardHeader>
            <CardTitle>要チェック馬リスト ({needsCheckHorses.length}件)</CardTitle>
            <p className="text-sm text-gray-500">
              ROIがマイナスの馬、名前が未決定の馬（〜の23等）、または競馬ブックURLが未登録の馬が表示されています。<br/>
              正しい競馬ブックの詳細ページURL（例: https://p.keibabook.co.jp/db/uma/123456）を入力して保存してください。
            </p>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="py-8 text-center text-gray-500">読み込み中...</div>
            ) : needsCheckHorses.length === 0 ? (
              <div className="py-8 text-center text-gray-500">要チェックの馬はありません。すべて正常です！</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">馬名</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">父</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">母</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">競馬ブックURL</th>
                      <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">操作</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {needsCheckHorses.map((horse) => {
                      const idStr = String(horse.id);
                      const currentUrl = editedUrls[idStr] !== undefined ? editedUrls[idStr] : (horse.keibabook_url || '');
                      const isSaving = saving[idStr];
                      
                      return (
                        <tr key={horse.id} className={!horse.keibabook_url ? 'bg-yellow-50' : ''}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            {horse.name || '不明'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {horse.sire || '-'}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {horse.dam || '-'}
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-500 w-full max-w-md">
                            <input
                              type="text"
                              value={currentUrl}
                              onChange={(e) => handleUrlChange(horse.id, e.target.value)}
                              placeholder="https://p.keibabook.co.jp/db/uma/..."
                              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                            />
                            {horse.keibabook_url && editedUrls[idStr] === undefined && (
                              <div className="mt-1 text-xs">
                                <a href={horse.keibabook_url} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">
                                  リンクを開く
                                </a>
                              </div>
                            )}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                            <Button 
                              onClick={() => handleSave(horse)} 
                              disabled={isSaving || (!currentUrl && !horse.keibabook_url)}
                              size="sm"
                              className={currentUrl && currentUrl !== horse.keibabook_url ? "bg-green-600 hover:bg-green-700" : ""}
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
