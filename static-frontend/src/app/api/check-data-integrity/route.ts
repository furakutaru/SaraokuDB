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
};

type HorseValidationRules = {
  [key: string]: FieldValidationRule;
};

type AuctionValidationRules = {
  [key: string]: FieldValidationRule;
};

interface ValidationRules {
  horse: HorseValidationRules;
  auction: AuctionValidationRules;
}

const FIELD_VALIDATIONS: ValidationRules = {
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
    disease_tags: { type: 'array', required: true, items: { type: 'string', required: true } },
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



// データ型を検証するヘルパー関数
function validateType(value: any, type: string | string[]): boolean {
  if (Array.isArray(type)) {
    return type.some(t => validateType(value, t));
  }

  if (value === null || value === undefined) {
    return type === 'null' || type === 'undefined';
  }

  switch (type) {
    case 'string': return typeof value === 'string';
    case 'number': return typeof value === 'number' && !isNaN(value);
    case 'boolean': return typeof value === 'boolean';
    case 'array': return Array.isArray(value);
    case 'object': return value !== null && typeof value === 'object' && !Array.isArray(value);
    case 'date': return !isNaN(Date.parse(value));
    case 'url': return typeof value === 'string' && /^https?:\/\//.test(value);
    default: return false;
  }
}

// 値の有効性をチェックするヘルパー関数
function isValidValue(
  value: any, 
  fieldName: keyof (HorseValidationRules & AuctionValidationRules), 
  type: 'horse' | 'auction' = 'horse'
): boolean {
  const validationRules = FIELD_VALIDATIONS[type];
  const fieldRule = validationRules[fieldName];
  
  if (!fieldRule) return true; // ルールが定義されていない場合は検証をスキップ
  
  // 値がnullまたはundefinedの場合
  if (value === null || value === undefined) {
    return !fieldRule.required; // 必須でない場合は有効
  }

  // 型チェック
  if (!validateType(value, fieldRule.type)) {
    return false;
  }

  // 最小値・最大値チェック
  if (typeof value === 'number') {
    if (fieldRule.min !== undefined && value < fieldRule.min) return false;
    if (fieldRule.max !== undefined && value > fieldRule.max) return false;
  }

  // 列挙値チェック
  if (fieldRule.enum && !fieldRule.enum.includes(value)) {
    return false;
  }

  // フォーマットチェック
  if (fieldRule.format === 'date' && !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    return false;
  }

  if (fieldRule.format === 'date-time' && isNaN(Date.parse(value))) {
    return false;
  }

  if (fieldRule.format === 'url' && !/^https?:\/\//.test(value)) {
    return false;
  }

  return true;
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
    
    // 各フィールドの検証
    for (const field of Object.keys(FIELD_VALIDATIONS.horse) as Array<keyof HorseValidationRules>) {
      const value = horse[field as keyof typeof horse];
      
      if (!isValidValue(value, field, 'horse')) {
        const rule = FIELD_VALIDATIONS.horse[field];
        let error = '';
        
        if (value === null || value === undefined || value === '') {
          error = '必須フィールドが空です';
        } else if (!validateType(value, rule.type)) {
          error = `型が一致しません。期待: ${rule.type}、実際: ${typeof value}`;
        } else if (rule.format === 'date' && !/^\d{4}-\d{2}-\d{2}$/.test(String(value))) {
          error = '日付の形式が正しくありません。YYYY-MM-DD形式で指定してください。';
        } else if (rule.format === 'date-time' && isNaN(Date.parse(String(value)))) {
          error = '日時の形式が正しくありません。ISO 8601形式で指定してください。';
        } else if (rule.format === 'url' && !/^https?:\/\//.test(String(value))) {
          error = 'URLの形式が正しくありません。http:// または https:// で始まる必要があります。';
        } else if (rule.enum && !rule.enum.includes(value as any)) {
          error = `無効な値です。許可されている値: ${rule.enum.join(', ')}`;
        } else if (typeof value === 'number') {
          if (rule.min !== undefined && value < rule.min) {
            error = `最小値は${rule.min}です。`;
          } else if (rule.max !== undefined && value > rule.max) {
            error = `最大値は${rule.max}です。`;
          }
        }
        
        issues.push({ field: field as string, issue: error, value });
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
    
    // 各フィールドの検証
    for (const field of Object.keys(FIELD_VALIDATIONS.auction) as Array<keyof AuctionValidationRules>) {
      const value = auction[field as keyof typeof auction];
      
      if (!isValidValue(value, field as keyof HorseValidationRules, 'auction')) {
        const rule = FIELD_VALIDATIONS.auction[field];
        let error = '';
        
        if (value === null || value === undefined || value === '') {
          error = '必須フィールドが空です';
        } else if (!validateType(value, rule.type)) {
          error = `型が一致しません。期待: ${rule.type}、実際: ${typeof value}`;
        } else if (rule.format === 'date' && !/^\d{4}-\d{2}-\d{2}$/.test(String(value))) {
          error = '日付の形式が正しくありません。YYYY-MM-DD形式で指定してください。';
        } else if (rule.format === 'date-time' && isNaN(Date.parse(String(value)))) {
          error = '日時の形式が正しくありません。ISO 8601形式で指定してください。';
        } else if (rule.format === 'url' && !/^https?:\/\//.test(String(value))) {
          error = 'URLの形式が正しくありません。http:// または https:// で始まる必要があります。';
        } else if (rule.enum && !rule.enum.includes(value as any)) {
          error = `無効な値です。許可されている値: ${rule.enum.join(', ')}`;
        } else if (typeof value === 'number') {
          if (rule.min !== undefined && value < rule.min) {
            error = `最小値は${rule.min}です。`;
          } else if (rule.max !== undefined && value > rule.max) {
            error = `最大値は${rule.max}です。`;
          }
        }
        
        issues.push({ field: field as string, issue: error, value });
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
