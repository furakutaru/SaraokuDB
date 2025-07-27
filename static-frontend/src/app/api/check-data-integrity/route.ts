import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const data = await request.json();
    
    // データの整合性チェックを実行
    const checkResult = await checkDataIntegrity(data);
    
    return NextResponse.json(checkResult);
  } catch (error) {
    console.error('データ整合性チェックエラー:', error);
    return NextResponse.json(
      { error: 'データの整合性チェック中にエラーが発生しました' },
      { status: 500 }
    );
  }
}

// フィールドのエイリアスマッピング
const FIELD_ALIASES: Record<string, string[]> = {
  'damsire': ['damsire', 'dam_sire'],
  'sire': ['sire'],
  'dam': ['dam'],
  'id': ['id'],
  'name': ['name'],
  'weight': ['weight'],
  'detail_url': ['detail_url'],
  'sex': ['sex'],
  'age': ['age'],
  'seller': ['seller'],
  'auction_date': ['auction_date'],
  'sold_price': ['sold_price'],
  'total_prize_start': ['total_prize_start'],
  'total_prize_latest': ['total_prize_latest'],
  'comment': ['comment'],
  'disease_tags': ['disease_tags'],
  'image_url': ['image_url', 'primary_image']
};

// 実際のフィールド名を取得するヘルパー関数
function getActualFieldName(obj: any, field: string): { name: string; value: any } | null {
  const aliases = FIELD_ALIASES[field] || [field];
  
  for (const alias of aliases) {
    if (alias in obj) {
      return { name: alias, value: obj[alias] };
    }
  }
  
  return null;
}

async function checkDataIntegrity(data: any) {
  const requiredFields = {
    basic: ['id', 'name', 'sire', 'dam', 'damsire', 'weight', 'detail_url'],
    history: ['sex', 'age', 'seller', 'auction_date', 'sold_price', 'total_prize_start', 'total_prize_latest', 'comment', 'disease_tags']
  };

  const results = {
    summary: {
      total_horses: 0,
      horses_with_issues: 0,
      total_issues: 0,
    },
    issues: [] as Array<{
      id: string;
      name: string;
      issues: Array<{ field: string; issue: string; value?: any }>;
    }>,
  };

  if (!data.horses || !Array.isArray(data.horses)) {
    throw new Error('無効なデータ形式です');
  }

  results.summary.total_horses = data.horses.length;

  for (const horse of data.horses) {
    const issues: Array<{ field: string; issue: string; value?: any }> = [];
    
    // 基本情報のチェック（トップレベル）
    for (const field of requiredFields.basic) {
      const fieldInfo = getActualFieldName(horse, field);
      if (!fieldInfo) {
        issues.push({ field, issue: 'フィールドが存在しません' });
      } else if (!isValidValue(fieldInfo.value, field)) {
        issues.push({ 
          field: fieldInfo.name, 
          issue: '無効な値です', 
          value: fieldInfo.value 
        });
      }
    }
    
    // 履歴情報のチェック
    if (horse.history && Array.isArray(horse.history) && horse.history.length > 0) {
      // 最新の履歴を取得
      const latestHistory = horse.history[horse.history.length - 1];
      
      // 未出走馬かどうかをチェック
      const isUnraced = latestHistory.comment?.includes('未出走') || 
                       latestHistory.race_record === '未出走' ||
                       latestHistory.race_record === '';
      
      // 履歴内の必須フィールドをチェック
      for (const field of requiredFields.history) {
        // 未出走馬の場合は賞金関連のチェックをスキップ
        if (isUnraced && (field === 'total_prize_start' || field === 'total_prize_latest')) {
          continue;
        }
        
        const fieldInfo = getActualFieldName(latestHistory, field);
        if (!fieldInfo) {
          // 未出走馬で賞金フィールドがなくてもエラーにしない
          if (!(isUnraced && (field === 'total_prize_start' || field === 'total_prize_latest'))) {
            issues.push({ field, issue: 'フィールドが存在しません' });
          }
        } else if (!isValidValue(fieldInfo.value, field)) {
          // 未出走馬で賞金が0でもエラーにしない
          if (!(isUnraced && (field === 'total_prize_start' || field === 'total_prize_latest') && 
               (fieldInfo.value === 0 || fieldInfo.value === null || fieldInfo.value === undefined))) {
            issues.push({ 
              field: fieldInfo.name, 
              issue: '無効な値です', 
              value: fieldInfo.value 
            });
          }
        }
      }
      
      // 画像URLのチェック（履歴またはトップレベル）
      const imageUrl = getActualFieldName(horse, 'image_url') || 
                      getActualFieldName(latestHistory, 'image_url');
      
      if (!imageUrl || !isValidValue(imageUrl.value, 'image_url')) {
        issues.push({ field: 'image_url', issue: '有効な画像URLが存在しません' });
      }
    } else {
      issues.push({ field: 'history', issue: '履歴情報が存在しません' });
    }
    
    if (issues.length > 0) {
      results.summary.horses_with_issues++;
      results.summary.total_issues += issues.length;
      
      results.issues.push({
        id: horse.id || '不明',
        name: horse.name || '不明',
        issues,
      });
    }
  }

  return results;
}

function isValidValue(value: any, fieldName: string): boolean {
  if (value === null || value === undefined) {
    return false;
  }
  
  if (typeof value === 'string' && !value.trim()) {
    return false;
  }
  
  if (Array.isArray(value) && value.length === 0) {
    return false;
  }
  
  if (fieldName === 'comment' && value === '取得できませんでした') {
    return false;
  }
  
  if (fieldName === 'disease_tags' && JSON.stringify(value) === JSON.stringify([''])) {
    return false;
  }
  
  return true;
}
