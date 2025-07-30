import { NextResponse } from 'next/server';
import path from 'path';
import fs from 'fs/promises';

// フィールドの検証ルール
type FieldValidationRule = {
  type: string | string[];
  required: boolean;
  min?: number;
  max?: number;
  enum?: any[];
  format?: string;
  items?: FieldValidationRule;
  [key: string]: any;
};

const FIELD_VALIDATIONS = {
  // 馬基本情報の検証ルール
  horse: {
    id: { type: 'string', required: true },
    name: { type: 'string', required: true },
    sex: { type: 'string', required: true, enum: ['牡', '牝', 'セ'] },
    age: { type: 'number', required: true, min: 0, max: 30 },
    color: { type: 'string', required: false },
    birthday: { type: 'string', required: false, format: 'date' },
    sire: { type: 'string', required: true },
    dam: { type: 'string', required: true },
    damsire: { type: 'string', required: true },
    image_url: { type: 'string', required: true, format: 'url' },
    jbis_url: { type: 'string', required: true, format: 'url' },
    auction_url: { type: 'string', required: true, format: 'url' },
    disease_tags: { type: 'array', required: true, items: { type: 'string' } },
    created_at: { type: 'string', required: true, format: 'date-time' },
    updated_at: { type: 'string', required: true, format: 'date-time' }
  },
  // オークション履歴の検証ルール
  auction: {
    id: { type: 'string', required: true },
    horse_id: { type: 'string', required: true },
    auction_date: { type: 'string', required: true, format: 'date' },
    sold_price: { type: ['number', 'null'], required: true, min: 0 },
    total_prize_start: { type: 'number', required: true, min: 0 },
    total_prize_latest: { type: 'number', required: true, min: 0 },
    is_unsold: { type: 'boolean', required: true },
    seller: { type: 'string', required: true },
    weight: { type: ['number', 'null'], required: true, min: 0 },
    comment: { type: 'string', required: false },
    created_at: { type: 'string', required: true, format: 'date-time' },
    updated_at: { type: 'string', required: true, format: 'date-time' }
  }
};

export async function POST(request: Request) {
  try {
    // データを直接ファイルから読み込む
    const projectRoot = process.cwd();
    const horsesPath = path.join(projectRoot, 'public', 'data', 'horses.json');
    const auctionHistoryPath = path.join(projectRoot, 'public', 'data', 'auction_history.json');
    
    const [horsesData, auctionHistoryData] = await Promise.all([
      fs.readFile(horsesPath, 'utf-8').then(JSON.parse),
      fs.readFile(auctionHistoryPath, 'utf-8').then(JSON.parse)
    ]);
    
    // データの整合性チェックを実行
    const checkResult = await checkDataIntegrity(horsesData, auctionHistoryData);
    
    return NextResponse.json(checkResult);
  } catch (error) {
    console.error('データ整合性チェックエラー:', error);
    return NextResponse.json(
      { error: 'データの整合性チェック中にエラーが発生しました: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

// フィールドの検証ルール
const FIELD_VALIDATIONS = {
  // 馬基本情報の検証ルール
  horse: {
    id: { type: 'string', required: true },
    name: { type: 'string', required: true },
    sex: { type: 'string', required: true, enum: ['牡', '牝', 'セ'] },
    age: { type: 'number', required: true, min: 0, max: 30 },
    color: { type: 'string', required: false },
    birthday: { type: 'string', required: false, format: 'date' },
    sire: { type: 'string', required: true },
    dam: { type: 'string', required: true },
    damsire: { type: 'string', required: true },
    image_url: { type: 'string', required: true, format: 'url' },
    jbis_url: { type: 'string', required: true, format: 'url' },
    auction_url: { type: 'string', required: true, format: 'url' },
    disease_tags: { type: 'array', required: true, items: { type: 'string' } },
    created_at: { type: 'string', required: true, format: 'date-time' },
    updated_at: { type: 'string', required: true, format: 'date-time' }
  },
  // オークション履歴の検証ルール
  auction: {
    id: { type: 'string', required: true },
    horse_id: { type: 'string', required: true },
    auction_date: { type: 'string', required: true, format: 'date' },
    sold_price: { type: ['number', 'null'], required: true, min: 0 },
    total_prize_start: { type: 'number', required: true, min: 0 },
    total_prize_latest: { type: 'number', required: true, min: 0 },
    is_unsold: { type: 'boolean', required: true },
    seller: { type: 'string', required: true },
    weight: { type: ['number', 'null'], required: true, min: 0 },
    comment: { type: 'string', required: false },
    created_at: { type: 'string', required: true, format: 'date-time' },
    updated_at: { type: 'string', required: true, format: 'date-time' }
  }
};

// データ型を検証するヘルパー関数
function validateType(value: any, type: string | string[]): boolean {
  if (Array.isArray(type)) {
    return type.some(t => validateType(value, t));
  }

  if (value === null || value === undefined) return false;
  
  switch (type) {
    case 'string': return typeof value === 'string';
    case 'number': return typeof value === 'number' && !isNaN(value);
    case 'boolean': return typeof value === 'boolean';
    case 'array': return Array.isArray(value);
    case 'date': return !isNaN(Date.parse(value));
    case 'date-time': return !isNaN(Date.parse(value));
    case 'url': 
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    default: return false;
  }
}

// データの整合性チェックを実行
async function checkDataIntegrity(horsesData: any, auctionHistoryData: any) {
  const results = {
    summary: {
      total_horses: 0,
      total_auctions: 0,
      horses_with_issues: 0,
      auctions_with_issues: 0,
      total_issues: 0,
    },
    horse_issues: [] as Array<{
      id: string;
      name: string;
      issues: Array<{ field: string; issue: string; value?: any }>;
    }>,
    auction_issues: [] as Array<{
      id: string;
      horse_id: string;
      issues: Array<{ field: string; issue: string; value?: any }>;
    }>,
    relationship_issues: {
      horses_without_auctions: [] as string[],
      auctions_without_horses: [] as string[],
      invalid_horse_references: [] as Array<{ auction_id: string; horse_id: string }>
    }
  };

  // 馬データの検証
  if (!horsesData?.horses || !Array.isArray(horsesData.horses)) {
    throw new Error('無効な馬データ形式です');
  }

  // オークションデータの検証
  if (!auctionHistoryData?.auction_history || !Array.isArray(auctionHistoryData.auction_history)) {
    throw new Error('無効なオークションデータ形式です');
  }

  const horseIds = new Set<string>();
  const auctionHorseIds = new Set<string>();

  // 馬データの検証
  results.summary.total_horses = horsesData.horses.length;
  for (const horse of horsesData.horses) {
    const issues: Array<{ field: string; issue: string; value?: any }> = [];
    
    // 各フィールドを検証
    for (const [field, rule] of Object.entries(FIELD_VALIDATIONS.horse)) {
      const value = horse[field];
      const fieldRule = rule as FieldValidationRule;
      
      // 必須フィールドチェック
      if (fieldRule.required && (value === undefined || value === null || value === '')) {
        issues.push({ field, issue: '必須フィールドがありません' });
        continue;
      }
      
      // 型チェック
      if (value !== undefined && value !== null && !validateType(value, fieldRule.type)) {
        issues.push({ 
          field, 
          issue: `無効な型です。期待: ${fieldRule.type}、実際: ${Array.isArray(value) ? 'array' : typeof value}`,
          value
        });
      }
      
      // 列挙値チェック
      if ('enum' in fieldRule && !fieldRule.enum?.includes(value)) {
        issues.push({
          field,
          issue: `無効な値です。許可された値: ${fieldRule.enum?.join(', ')}`,
          value
        });
      }
      
      // 最小値/最大値チェック
      if (typeof value === 'number') {
        if ('min' in fieldRule && value < (fieldRule.min as number)) {
          issues.push({
            field,
            issue: `最小値は${fieldRule.min}である必要があります`,
            value
          });
        }
        if ('max' in fieldRule && value > (fieldRule.max as number)) {
          issues.push({
            field,
            issue: `最大値は${fieldRule.max}である必要があります`,
            value
          });
        }
      }
    }
    
    if (issues.length > 0) {
      results.summary.horses_with_issues++;
      results.summary.total_issues += issues.length;
      results.horse_issues.push({
        id: horse.id,
        name: horse.name || '名前不明',
        issues
      });
    }
    
    if (horse.id) {
      horseIds.add(horse.id);
    }
  }
  
  // オークションデータの検証
  results.summary.total_auctions = auctionHistoryData.auction_history.length;
  for (const auction of auctionHistoryData.auction_history) {
    const issues: Array<{ field: string; issue: string; value?: any }> = [];
    
    // 各フィールドを検証
    for (const [field, rule] of Object.entries(FIELD_VALIDATIONS.auction)) {
      const value = auction[field];
      const fieldRule = rule as FieldValidationRule;
      
      // 必須フィールドチェック
      if (fieldRule.required && (value === undefined || value === null || value === '')) {
        issues.push({ field, issue: '必須フィールドがありません' });
        continue;
      }
      
      // 型チェック
      if (value !== undefined && value !== null && !validateType(value, fieldRule.type)) {
        issues.push({ 
          field, 
          issue: `無効な型です。期待: ${fieldRule.type}、実際: ${Array.isArray(value) ? 'array' : typeof value}`,
          value
        });
      }
      
      // 最小値/最大値チェック
      if (typeof value === 'number') {
        if ('min' in fieldRule && value < (fieldRule.min as number)) {
          issues.push({
            field,
            issue: `最小値は${fieldRule.min}である必要があります`,
            value
          });
        }
        if ('max' in fieldRule && value > (fieldRule.max as number)) {
          issues.push({
            field,
            issue: `最大値は${fieldRule.max}である必要があります`,
            value
          });
        }
      }
    }
    
    if (issues.length > 0) {
      results.summary.auctions_with_issues++;
      results.summary.total_issues += issues.length;
      results.auction_issues.push({
        id: auction.id || '不明',
        horse_id: auction.horse_id || '不明',
        issues
      });
    }
    
    if (auction.horse_id) {
      auctionHorseIds.add(auction.horse_id);
    }
  }
  
  // リレーションシップの整合性チェック
  for (const id of horseIds) {
    if (!auctionHorseIds.has(id)) {
      const horse = horsesData.horses.find((h: any) => h.id === id);
      results.relationship_issues.horses_without_auctions.push(horse?.name || id);
      results.summary.total_issues++;
    }
  }
  
  for (const id of auctionHorseIds) {
    if (!horseIds.has(id)) {
      results.relationship_issues.auctions_without_horses.push(id);
      results.summary.total_issues++;
    }
  }
  
  // 無効な馬ID参照のチェック
  for (const auction of auctionHistoryData.auction_history) {
    if (auction.horse_id && !horseIds.has(auction.horse_id)) {
      results.relationship_issues.invalid_horse_references.push({
        auction_id: auction.id || '不明',
        horse_id: auction.horse_id
      });
    }
  }
  
  return results;
}

type FieldValidationRule = {
  type: string | string[];
  required: boolean;
  min?: number;
  max?: number;
  enum?: any[];
  format?: string;
  items?: FieldValidationRule;
  [key: string]: any;
};

function validateType(value: any, type: string | string[]): boolean {
  if (Array.isArray(type)) {
    return type.some(t => validateType(value, t));
  }

  if (value === null || value === undefined) return false;
  
  switch (type) {
    case 'string': return typeof value === 'string';
    case 'number': return typeof value === 'number' && !isNaN(value);
    case 'boolean': return typeof value === 'boolean';
    case 'array': return Array.isArray(value);
    case 'date': return !isNaN(Date.parse(value));
    case 'date-time': return !isNaN(Date.parse(value));
    case 'url': 
      try {
        new URL(value);
        return true;
      } catch {
        return false;
      }
    default: return false;
  }
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
