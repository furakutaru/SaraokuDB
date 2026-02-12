import { matchHorseCandidate, normalizeId, normalizeName } from './ids';
import { buildUIHorse, HorseUI } from './horseMap';

// Types aligned with current pages (keep UI contracts unchanged)
export interface HorseHistoryUI {
  auction_date: string;
  name: string;
  sex: string;
  age: string;
  seller: string;
  race_record: string;
  comment: string;
  sold_price: number | null;
  total_prize_start: number;
  unsold?: boolean;
  detail_url?: string;
  primary_image?: string;
  disease_tags?: string;
  weight?: number;
}

// HorseUI is imported from horseMap

export interface HorsesListResponse {
  horses: any[];
  // バックエンドのレスポンスに合わせて両方のパターンをサポート
  auctionHistories?: any[];
  auction_histories?: any[];
  metadata: {
    last_updated: string;
    total_horses: number;
    total_auction_records: number;
    [key: string]: any;  // その他のプロパティも許容
  };
  [key: string]: any;  // その他のプロパティも許容
}

function apiBase(): string {
  return process.env.NEXT_PUBLIC_API_URL || 'https://saraokudb.onrender.com';
}

export async function fetchHorsesList(): Promise<HorsesListResponse> {
  const url = `${apiBase()}/api/horses?_=${Date.now()}`;
  console.log('[horseApi] fetch list:', url);
  
  try {
    console.log('[horseApi] リクエストを開始します...');
    const startTime = Date.now();
    
    const res = await fetch(url, { 
      headers: { 
        'Accept': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0'
      },
      cache: 'no-store' 
    });
    
    const responseTime = Date.now() - startTime;
    console.log(`[horseApi] レスポンス受信 (${responseTime}ms)`, { status: res.status, statusText: res.statusText });
    
    if (!res.ok) {
      const text = await res.text();
      console.error('[horseApi] エラーレスポンス:', { status: res.status, text });
      throw new Error(`データの取得に失敗しました (${res.status}): ${text}`);
    }
    
    const responseData = await res.json();
    console.log('[horseApi] レスポンスデータの構造:', {
      isArray: Array.isArray(responseData),
      hasHorses: 'horses' in responseData,
      hasAuctionHistories: 'auction_histories' in responseData,
      hasMetadata: 'metadata' in responseData,
      firstItem: Array.isArray(responseData) ? responseData[0] : null,
      rawKeys: responseData ? Object.keys(responseData) : []
    });
    
    // レスポンスデータの詳細なログを出力
    console.log('[horseApi] レスポンスデータの詳細:', {
      responseData: responseData,
      firstHorse: responseData?.horses?.[0],
      firstAuctionHistory: responseData?.auction_histories?.[0] || responseData?.auctionHistories?.[0],
      // 最初の馬の全プロパティをログに出力
      firstHorseKeys: responseData?.horses?.[0] ? Object.keys(responseData.horses[0]) : []
    });
    
    // デバッグ: 最初の数件の馬のdetail_urlとauction_urlをログに出力
    if (responseData?.horses) {
      const sampleHorses = responseData.horses.slice(0, 5);
      console.log('[horseApi] サンプル馬のURL情報:', 
        sampleHorses.map((h: any) => ({
          id: h.id,
          name: h.name,
          detail_url: h.detail_url,
          auction_url: h.auction_url,
          hasDetailUrl: !!h.detail_url,
          hasAuctionUrl: !!h.auction_url
        }))
      );
    }
    
    // レスポンスが配列の場合は、それをhorsesとして扱う
    let horses: any[] = [];
    let auctionHistories: any[] = [];
    let metadata = {
      last_updated: new Date().toISOString(),
      total_horses: 0,
      total_auction_records: 0
    };
    
    if (Array.isArray(responseData)) {
      // レスポンスが配列の場合は、それをhorsesとして扱う
      horses = responseData.map(record => ({
        id: record.id || record.horse_id || Math.random().toString(36).substr(2, 9),
        name: record.name || `馬名不明 (ID: ${record.id || record.horse_id || '不明'})`,
        raw_name: record.raw_name || null,
        sex: record.sex || '不明',
        age: record.age || 0,
        sire: record.sire || '不明',
        dam: record.dam || '不明',
        damsire: record.damsire || record.dam_sire || '不明',
        image_url: record.image_url || '',
        jbis_url: record.jbis_url || '',
        auction_url: record.auction_url || '',
        disease_tags: Array.isArray(record.disease_tags) 
          ? record.disease_tags 
          : (record.disease_tags ? [record.disease_tags] : []),
        weight: record.weight || null,
        race_record: record.race_record || '',
        comment: record.comment || '',
        created_at: record.created_at || new Date().toISOString(),
        updated_at: record.updated_at || new Date().toISOString(),
        sold_price: record.sold_price || null,
        seller: record.seller || '不明',
        auction_date: record.auction_date || null,
        total_prize_start: record.total_prize_start || 0,
        total_prize_latest: record.total_prize_latest || 0,
        is_unsold: record.is_unsold || record.unsold || false,
        is_broodmare: Boolean(record.is_broodmare)
      }));
      
      metadata = {
        last_updated: new Date().toISOString(),
        total_horses: horses.length,
        total_auction_records: horses.length
      };
    } else if (responseData && typeof responseData === 'object') {
      // オブジェクトの場合は、期待される構造にマッピング
      horses = Array.isArray(responseData.horses) 
        ? responseData.horses 
        : [];
        
      auctionHistories = Array.isArray(responseData.auction_histories) 
        ? responseData.auction_histories 
        : [];
        
      metadata = {
        last_updated: responseData.metadata?.last_updated || new Date().toISOString(),
        total_horses: responseData.metadata?.total_horses !== undefined 
          ? responseData.metadata.total_horses 
          : horses.length,
        total_auction_records: responseData.metadata?.total_auction_records !== undefined
          ? responseData.metadata.total_auction_records
          : auctionHistories.length
      };
    }
    
    console.log('[horseApi] 処理完了:', {
      horsesCount: horses.length,
      auctionHistoriesCount: auctionHistories.length,
      metadata
    });
    
    return {
      horses,
      auctionHistories,
      metadata
    };
  } catch (error) {
    console.error('[horseApi] フェッチエラー:', error);
    throw new Error(`データの取得中にエラーが発生しました: ${error instanceof Error ? error.message : String(error)}`);
  }
}

// buildUIHorse is imported

export async function getHorseData(horseIdRaw: string): Promise<{ horse: HorseUI | null; error: string | null }> {
  console.log('[getHorseData] 開始. 入力ID:', horseIdRaw);
  const horseId = normalizeId(horseIdRaw);
  console.log('[getHorseData] 正規化後ID:', horseId);
  
  if (!horseId) {
    console.error('[getHorseData] 無効な馬IDです');
    return { horse: null, error: '無効な馬IDです' };
  }

  // 1. 詳細APIから取得を試みる
  const detailUrl = `${apiBase()}/api/horses/${encodeURIComponent(horseId)}?_=${Date.now()}`;
  console.log('[getHorseData] 詳細APIを呼び出します:', detailUrl);
  
  try {
    const res = await fetch(detailUrl, { 
      headers: { 
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }, 
      cache: 'no-store' 
    });
    
    console.log('[getHorseData] レスポンスステータス:', res.status);
    
    if (res.ok) {
      const base = await res.json();
      console.log('[getHorseData] 詳細APIレスポンス:', base);
      const horse = buildUIHorse(base, horseId);
      console.log('[getHorseData] ビルド後の馬データ:', horse);
      return { horse, error: null };
    }
    
    if (res.status !== 404) {
      const text = await res.text();
      console.error('[getHorseData] エラーが発生しました:', res.status, text);
      return { horse: null, error: '馬データの取得に失敗しました' };
    }
    
    console.log('[getHorseData] 404エラーのため、リストからの取得を試みます');
    
    // 2. リストAPIから取得を試みる
    const listUrl = `${apiBase()}/api/horses?limit=10000&_=${Date.now()}`;
    console.warn('[getHorseData] リストAPIを呼び出します:', listUrl);
    
    const listRes = await fetch(listUrl, { 
      headers: { 
        'Accept': 'application/json',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
      }, 
      cache: 'no-store' 
    });
    
    if (listRes.ok) {
      const list = await listRes.json();
      console.log('[getHorseData] リストAPIレスポンスを取得しました。馬の数:', list?.horses?.length || 0);
      
      const horses: any[] = Array.isArray(list?.horses) ? list.horses : [];
      const numId = Number(horseId);
      
      // 候補を検索
      let candidate = horses.find(h => {
        const idMatch = h.id === horseId || 
                       (typeof h.id === 'number' && !Number.isNaN(numId) && h.id === numId) ||
                       (h.auction_id && String(h.auction_id) === horseId);
        
        if (idMatch) {
          console.log('[getHorseData] リストから一致する馬を発見:', h.id, h.name);
        }
        return idMatch;
      });

      if (candidate) {
        console.log('[getHorseData] リストから馬データを取得しました:', candidate.id, candidate.name);
        return { horse: buildUIHorse(candidate, horseId), error: null };
      }
    }
    
    // 3. 静的ファイルから取得を試みる
    console.log('[getHorseData] 静的ファイルからの取得を試みます');
    try {
      const staticUrl = (typeof window !== 'undefined')
        ? new URL('/data/horses.json', window.location.origin).toString()
        : '/data/horses.json';
      
      console.log('[getHorseData] 静的ファイルを取得:', staticUrl);
      const staticRes = await fetch(staticUrl, { cache: 'no-store' });
      
      if (staticRes.ok) {
        const staticHorses = await staticRes.json();
        console.log('[getHorseData] 静的ファイルを取得しました。馬の数:', staticHorses?.length || 0);
        
        const staticBase = Array.isArray(staticHorses)
          ? staticHorses.find((h: any) => String(h.id) === horseId || String(h.auction_id) === horseId)
          : null;
          
        if (staticBase) {
          console.log('[getHorseData] 静的ファイルから馬データを取得しました:', staticBase.id, staticBase.name);
          return { horse: buildUIHorse(staticBase, horseId), error: null };
        }
      }
    } catch (staticError) {
      console.error('[getHorseData] 静的ファイルの取得中にエラーが発生しました:', staticError);
    }
    
    console.error('[getHorseData] どの方法でも馬データを見つけることができませんでした');
    return { horse: null, error: '馬のデータが見つかりません' };
    
  } catch (error) {
    console.error('[getHorseData] 例外が発生しました:', error);
    return { horse: null, error: 'データの取得中にエラーが発生しました' };
  }
}
