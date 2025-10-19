const fs = require('fs');
const path = require('path');

// ファイルパスの設定
const dataDir = path.join(__dirname, '../public/data');
const horsesPath = path.join(dataDir, 'horses.json');
const auctionHistoryPath = path.join(dataDir, 'auction_history.json');
const outputPath = path.join(dataDir, 'horses_combined.json');

// データを読み込む
const horses = JSON.parse(fs.readFileSync(horsesPath, 'utf-8'));
const auctionHistory = JSON.parse(fs.readFileSync(auctionHistoryPath, 'utf-8'));

// メタデータを準備
const metadata = {
  version: '1.1',
  last_updated: new Date().toISOString(),
  total_horses: horses.length,
  data_source: 'jbis'
};

// 馬データを新しい形式に変換
const combinedHorses = horses.map(horse => {
  // 賞金を数値に変換（より堅牢な処理に変更）
  let prizeMoney = 0;
  try {
    if (horse.prize_money?.total_prize) {
      const prizeStr = String(horse.prize_money.total_prize);
      prizeMoney = parseInt(prizeStr.replace(/[^0-9]/g, '')) || 0;
    }
  } catch (e) {
    console.warn(`賞金のパースエラー (horse.id: ${horse.id}):`, e.message);
    prizeMoney = 0;
  }

  // オークション履歴を処理
  const auctionHistory = [];
  if (horse.auction_history && horse.auction_history.length > 0) {
    auctionHistory.push(...horse.auction_history.map(ah => ({
      date: ah.auction_date || ah.date,
      price: ah.sold_price || ah.price,
      weight: ah.weight,
      seller: ah.seller,
      is_unsold: ah.is_unsold || false,
      comment: ah.comment || '',
      auction_date: ah.auction_date || ah.date,
      total_prize_start: ah.total_prize_start,
      total_prize_latest: ah.total_prize_latest
    })));
  }

  // 基本情報を設定
  const basicInfo = {
    name: horse.name,
    id: horse.id,
    auction_id: horse.auction_id,
    detail_url: horse.detail_url,
    sex: horse.sex,
    age: horse.age,
    sire: horse.sire,
    dam: horse.dam,
    damsire: horse.damsire,
    auction_date: horse.auction_date,
    weight: horse.weight,
    jbis_url: horse.jbis_url,
    prize_money: horse.prize_money,
    comment: horse.comment,
    disease_tags: horse.disease_tags || []
  };

  // オークション履歴を取得
  const horseAuctionHistory = auctionHistory
    .filter(ah => ah.horse_id === horse.id)
    .map(ah => ({
      auction_date: ah.auction_date || ah.date,
      price: ah.sold_price || ah.price,
      weight: ah.weight,
      seller: ah.seller,
      is_unsold: ah.is_unsold || false,
      comment: ah.comment || ''
    }));

  // 最新のオークション情報
  const latestAuction = horseAuctionHistory.length > 0 
    ? horseAuctionHistory[0] 
    : null;

  // レース記録を初期化（必要に応じて調整）
  const raceRecords = [];

  // メタデータ
  const horseMetadata = {
    created_at: horse.created_at || new Date().toISOString(),
    updated_at: new Date().toISOString(),
    data_source: 'jbis'
  };

  return {
    id: horse.id,
    basic_info: basicInfo,
    race_records: raceRecords,
    auction_history: horseAuctionHistory,
    latest_auction: latestAuction,
    metadata: horseMetadata
  };
});

// 出力用データ
const outputData = {
  metadata,
  horses: combinedHorses
};

// ファイルに書き出し
fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2));

console.log(`データの統合が完了しました。出力先: ${outputPath}`);
