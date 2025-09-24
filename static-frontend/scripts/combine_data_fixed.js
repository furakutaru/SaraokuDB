const fs = require('fs');
const path = require('path');

// ファイルパスの設定
const dataDir = path.join(__dirname, '../public/data');
const horsesPath = path.join(dataDir, 'horses.json');
const auctionHistoryPath = path.join(dataDir, 'auction_history.json');
const outputPath = path.join(dataDir, 'horses_combined.json');

// エラーログ用の関数
const logError = (message, error) => {
  const timestamp = new Date().toISOString();
  const logMessage = `[${timestamp}] ${message}: ${error ? error.message : ''}\n`;
  fs.appendFileSync(path.join(dataDir, 'combine_errors.log'), logMessage);
  console.error(logMessage);
};

try {
  // データを読み込む
  const horses = JSON.parse(fs.readFileSync(horsesPath, 'utf-8'));
  const auctionHistory = JSON.parse(fs.readFileSync(auctionHistoryPath, 'utf-8'));

  // メタデータを準備
  const metadata = {
    version: '1.2',
    last_updated: new Date().toISOString(),
    total_horses: horses.length,
    data_source: 'jbis',
    generated_by: 'combine_data_fixed.js'
  };

  // 賞金をパースするヘルパー関数
  const parsePrizeMoney = (prizeData) => {
    try {
      if (!prizeData) return 0;
      if (typeof prizeData === 'number') return prizeData;
      if (typeof prizeData === 'string') {
        return parseInt(prizeData.replace(/[^0-9]/g, '')) || 0;
      }
      if (prizeData.total_prize) {
        return parsePrizeMoney(prizeData.total_prize);
      }
      return 0;
    } catch (error) {
      logError('Error parsing prize money', error);
      return 0;
    }
  };

  // 馬データを新しい形式に変換
  const combinedHorses = horses.map(horse => {
    try {
      // 賞金を数値に変換
      const prizeMoney = parsePrizeMoney(horse.prize_money);

      // オークション履歴を処理
      const auctionHistoryForHorse = auctionHistory
        .filter(ah => ah.horse_id === horse.id)
        .sort((a, b) => new Date(b.auction_date) - new Date(a.auction_date)); // 日付の新しい順にソート
      
      // オークション履歴を整形
      const formattedAuctionHistory = auctionHistoryForHorse.map(ah => ({
        id: ah.id,
        date: ah.auction_date,
        price: ah.sold_price,
        weight: ah.weight,
        seller: ah.seller,
        is_unsold: ah.is_unsold || false,
        comment: ah.comment || '',
        auction_date: ah.auction_date,
        total_prize_start: ah.total_prize_start || 0,
        total_prize_latest: ah.total_prize_latest || 0,
        created_at: ah.created_at || new Date().toISOString()
      }));

      // 最新のオークション情報
      const latestAuction = formattedAuctionHistory.length > 0 
        ? formattedAuctionHistory[0] 
        : null;

      // コメントを統合（馬情報とオークション情報のコメントを結合）
      const combinedComment = [
        horse.comment,
        ...formattedAuctionHistory.map(ah => ah.comment).filter(Boolean)
      ].filter(Boolean).join('\n\n---\n\n');

      // 基本情報
      const basicInfo = {
        name: horse.name,
        sex: horse.sex,
        age: horse.age,
        sire: horse.sire,
        dam: horse.dam,
        damsire: horse.damsire,
        image_url: typeof horse.image_url === 'object' ? horse.image_url?.image_url : horse.image_url,
        jbis_url: horse.jbis_url,
        auction_url: horse.detail_url || horse.auction_url,
        is_retired: false,
        retirement_date: null,
        disease_tags: Array.isArray(horse.disease_tags) ? horse.disease_tags : []
      };

      // 最新の馬体重を取得（オークション履歴から最新の有効な体重を取得）
      const latestWeight = formattedAuctionHistory
        .filter(ah => ah.weight !== null && ah.weight !== undefined)
        .sort((a, b) => new Date(b.date) - new Date(a.date))[0]?.weight || horse.weight || null;

      // 馬データを整形
      return {
        id: horse.id,
        ...basicInfo, // 基本情報を展開
        comment: combinedComment, // 統合されたコメント
        weight: latestWeight, // 最新の馬体重を設定
        is_unsold: latestAuction?.is_unsold || horse.is_unsold || false,
        sold_price: latestAuction?.price || horse.sold_price || null,
        auction_date: latestAuction?.auction_date || horse.auction_date || null,
        seller: latestAuction?.seller || horse.seller || '',
        basic_info: basicInfo, // 基本情報オブジェクト
        race_records: {
          total_prize_money: prizeMoney,
          last_race_date: horse.last_race_date || null,
          last_prize_update: horse.last_prize_update || new Date().toISOString()
        },
        auction_history: formattedAuctionHistory,
        latest_auction: latestAuction,
        metadata: {
          created_at: horse.created_at || new Date().toISOString(),
          updated_at: new Date().toISOString(),
          data_source: horse.data_source || 'jbis',
          original_data: {
            has_image: !!horse.image_url,
            has_jbis_url: !!horse.jbis_url,
            auction_history_count: formattedAuctionHistory.length
          }
        }
      };
    } catch (error) {
      logError(`Error processing horse ${horse.id || 'unknown'}`, error);
      return null; // エラーが発生した場合はnullを返し、後でフィルタリング
    }
  }).filter(horse => horse !== null); // エラーが発生した馬をフィルタリング

  // 出力用データ
  const outputData = {
    metadata,
    horses: combinedHorses,
    statistics: {
      total_horses: combinedHorses.length,
      with_auction_history: combinedHorses.filter(h => h.auction_history.length > 0).length,
      with_images: combinedHorses.filter(h => h.basic_info.image_url).length,
      last_updated: new Date().toISOString()
    }
  };

  // バックアップを作成
  const backupPath = `${outputPath}.${new Date().toISOString().replace(/[:.]/g, '-')}.bak`;
  if (fs.existsSync(outputPath)) {
    fs.copyFileSync(outputPath, backupPath);
    console.log(`Created backup at: ${backupPath}`);
  }

  // ファイルに書き出し
  fs.writeFileSync(outputPath, JSON.stringify(outputData, null, 2));
  console.log(`Successfully combined data for ${combinedHorses.length} horses.`);

} catch (error) {
  logError('Fatal error in combine_data_fixed.js', error);
  process.exit(1);
}

console.log(`データの統合が完了しました。出力先: ${outputPath}`);
