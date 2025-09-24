const fs = require('fs');
const path = require('path');

// 入力ファイルと出力ファイルのパス
const inputFile = path.join(__dirname, '../static-frontend/public/data/horses_combined.json');
const outputFile = path.join(__dirname, '../static-frontend/public/data/horses_history.json');

// メタデータを生成
function generateMetadata(horses) {
  const now = new Date().toISOString();
  const prices = horses
    .filter(horse => horse.sold_price && !isNaN(parseInt(horse.sold_price)))
    .map(horse => parseInt(horse.sold_price));
  
  const totalPrice = prices.reduce((sum, price) => sum + price, 0);
  const averagePrice = prices.length > 0 ? Math.round(totalPrice / prices.length) : 0;
  
  return {
    last_updated: now,
    total_horses: horses.length,
    average_price: averagePrice,
    version: '1.0',
    source: 'horses_combined.json',
    transformed_at: now
  };
}

// 馬の履歴データを生成
function transformHorse(horse) {
  // 基本情報
  const baseInfo = {
    id: horse.id,
    name: horse.name,
    sex: horse.sex,
    age: horse.age.toString(),
    color: '',
    birthday: '',
    sire: horse.sire || '',
    dam: horse.dam || '',
    dam_sire: horse.damsire || '',
    primary_image: horse.image_url || '',
    disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags.join(',') : horse.disease_tags || '',
    jbis_url: horse.jbis_url || '',
    weight: horse.weight || null,
    is_retired: horse.is_retired || false,
    retirement_date: horse.retirement_date || null,
    // その他の基本情報
    ...horse
  };

  // オークション履歴
  const history = [];
  
  // メインのオークション情報を履歴に追加
  if (horse.auction_date || horse.sold_price !== undefined) {
    history.push({
      auction_date: horse.auction_date || new Date().toISOString().split('T')[0],
      name: horse.name,
      sex: horse.sex,
      age: horse.age.toString(),
      seller: horse.seller || '',
      race_record: '',
      comment: horse.comment || '',
      sold_price: horse.sold_price || null,
      total_prize_start: 0, // 初期値
      unsold: horse.is_unsold || false,
      detail_url: horse.auction_url || '',
      primary_image: horse.image_url || '',
      disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags.join(',') : horse.disease_tags || '',
      weight: horse.weight || null
    });
  }

  // 追加のオークション履歴があれば追加
  if (horse.auction_history && Array.isArray(horse.auction_history)) {
    horse.auction_history.forEach(auction => {
      history.push({
        auction_date: auction.auction_date || auction.date || new Date().toISOString().split('T')[0],
        name: horse.name,
        sex: horse.sex,
        age: horse.age.toString(),
        seller: auction.seller || '',
        race_record: '',
        comment: auction.comment || horse.comment || '',
        sold_price: auction.price || auction.sold_price || null,
        total_prize_start: auction.total_prize_start || 0,
        unsold: auction.is_unsold || false,
        detail_url: horse.auction_url || '',
        primary_image: auction.image_url || horse.image_url || '',
        disease_tags: Array.isArray(auction.disease_tags) ? 
          auction.disease_tags.join(',') : 
          (auction.disease_tags || (Array.isArray(horse.disease_tags) ? horse.disease_tags.join(',') : horse.disease_tags || '')),
        weight: auction.weight || horse.weight || null
      });
    });
  }

  // 履歴が空の場合はデフォルトの履歴を追加
  if (history.length === 0) {
    history.push({
      auction_date: new Date().toISOString().split('T')[0],
      name: horse.name,
      sex: horse.sex,
      age: horse.age.toString(),
      seller: '',
      race_record: '',
      comment: horse.comment || '',
      sold_price: horse.sold_price || null,
      total_prize_start: 0,
      unsold: horse.is_unsold || false,
      detail_url: horse.auction_url || '',
      primary_image: horse.image_url || '',
      disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags.join(',') : horse.disease_tags || '',
      weight: horse.weight || null
    });
  }

  return {
    ...baseInfo,
    history: history
  };
}

// データを読み込んで変換
fs.readFile(inputFile, 'utf8', (err, data) => {
  if (err) {
    console.error('ファイルの読み込み中にエラーが発生しました:', err);
    return;
  }

  try {
    const inputData = JSON.parse(data);
    const horses = Array.isArray(inputData.horses) ? inputData.horses : [];
    
    // 各馬のデータを変換
    const transformedHorses = horses.map(horse => transformHorse(horse));
    
    // 最終的なデータ構造
    const transformedData = {
      metadata: generateMetadata(transformedHorses),
      horses: horses
    };

    // 変換したデータを保存
    fs.writeFile(outputFile, JSON.stringify(transformedData, null, 2), 'utf8', (err) => {
      if (err) {
        console.error('ファイルの保存中にエラーが発生しました:', err);
        return;
      }
      console.log(`データを変換して ${outputFile} に保存しました`);
    });
  } catch (err) {
    console.error('JSONのパース中にエラーが発生しました:', err);
  }
});
