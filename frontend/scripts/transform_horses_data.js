const fs = require('fs');
const path = require('path');

// ファイルパスの設定
const dataDir = path.join(__dirname, '../public/data');
const inputPath = path.join(dataDir, 'horses_combined.json');
const outputPath = path.join(dataDir, 'horses_transformed.json');

// データを読み込む
const rawData = JSON.parse(fs.readFileSync(inputPath, 'utf-8'));

// horses_combined.json が配列形式でもオブジェクト形式でも対応
const data = Array.isArray(rawData) ? { horses: rawData } : (rawData.horses ? rawData : { horses: [] });

// データを変換
const transformedHorses = data.horses.map(horse => {
  // オークション履歴を変換
  const history = (horse.auction_history || []).map(auction => ({
    auction_date: auction.auction_date || auction.date,
    name: horse.name,
    sex: horse.sex,
    age: horse.age,
    seller: auction.seller,
    race_record: '', // 必要に応じて設定
    comment: auction.comment || horse.comment || '',
    sold_price: auction.price || auction.sold_price,
    total_prize_start: auction.total_prize_start,
    unsold: auction.is_unsold,
    detail_url: horse.auction_url,
    primary_image: horse.image_url,
    disease_tags: horse.disease_tags || [],
    weight: auction.weight
  }));

  // オークション履歴がない場合は現在の情報から1件作成
  if (history.length === 0) {
    history.push({
      auction_date: horse.auction_date,
      name: horse.name,
      sex: horse.sex,
      age: horse.age,
      seller: horse.seller,
      race_record: '',
      comment: horse.comment || '',
      sold_price: horse.sold_price,
      total_prize_start: horse.total_prize_start,
      unsold: horse.is_unsold,
      detail_url: horse.auction_url,
      primary_image: horse.image_url,
      disease_tags: horse.disease_tags || [],
      weight: horse.weight
    });
  }

  // 馬データを変換
  return {
    id: horse.id,
    name: horse.name,
    sex: horse.sex,
    age: horse.age.toString(),
    color: '', // 必要に応じて設定
    birthday: '', // 必要に応じて設定
    history: history,
    sire: horse.sire,
    dam: horse.dam,
    dam_sire: horse.damsire,
    primary_image: horse.image_url,
    disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags.join(',') : horse.disease_tags || '',
    // その他の必要なフィールド
    ...horse
  };
});

// 出力用データ
const outputData = {
  metadata: {
    ...data.metadata,
    version: '1.3',
    last_updated: new Date().toISOString(),
    transformed: true
  },
  horses: transformedHorses
};

// ファイルに書き出し
fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2));
console.log(`データの変換が完了しました。出力先: ${outputPath}`);
