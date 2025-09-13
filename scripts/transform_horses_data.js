const fs = require('fs');
const path = require('path');

// 入力ファイルと出力ファイルのパス
const inputFile = path.join(__dirname, '../static-frontend/public/data/horses.json');
const outputFile = path.join(__dirname, '../static-frontend/public/data/horses_history.json');

// メタデータを生成
function generateMetadata(horses) {
  const now = new Date().toISOString();
  return {
    last_updated: now,
    total_horses: horses.length,
    average_price: 0, // 後で計算
    average_growth_rate: 0, // 後で計算
    horses_with_growth_data: 0 // 後で計算
  };
}

// データを読み込んで変換
fs.readFile(inputFile, 'utf8', (err, data) => {
  if (err) {
    console.error('ファイルの読み込み中にエラーが発生しました:', err);
    return;
  }

  try {
    const horses = JSON.parse(data);
    const transformedData = {
      metadata: generateMetadata(horses),
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
