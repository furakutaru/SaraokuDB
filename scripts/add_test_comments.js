const fs = require('fs');
const path = require('path');

// テスト用のコメントデータ
const testComments = [
  "テスト用のコメントです。\nこの馬はダノンスマッシュ産駒で、スリーカーニバルの2023年生まれの牝馬です。\n\n【調教状況】\n・7/20追い切り: 5F 1:02.5 (34.0-12.7)\n・7/15坂路: 5F 1:04.1 (36.3-13.0)\n\n【特徴】\n・バランスの良い馬体\n・柔らかい動きが特徴\n・気性はおだやか\n\n【所見】\n調教の進み具合は順調で、仕上がりは7割程度。レースに使える状態まではあと1-2週間かかりそうです。",
  "2頭目のテストコメントです。\nこの馬は父モズアスコット、母クラウンドジャックの2023年生まれの牡馬です。\n\n【調教状況】\n・7/22追い切り: 5F 1:03.0 (34.5-12.8)\n・7/17坂路: 5F 1:04.5 (36.8-13.2)\n\n【特徴】\n・パワフルな走り\n・スタミナに優れる\n・気性はやや激しい\n\n【所見】\nパワーは十分だが、コントロールに課題あり。レースデビューまでにはもう少し時間がかかりそう。",
  "3頭目のテストコメントです。\nこの馬は父キタサンブラック、母サマーリガードの2023年生まれの牝馬です。\n\n【調教状況】\n・7/21追い切り: 5F 1:02.8 (34.3-12.6)\n・7/16坂路: 5F 1:04.3 (36.5-13.1)\n\n【特徴】\n・スピードに優れる\n・切れ味抜群\n・気性はおとなしい\n\n【所見】\nスピードは申し分ないが、スタミナにやや不安あり。短距離戦向きの馬。"
];

// ファイルパス
const filePath = path.join(__dirname, '../static-frontend/public/data/horses_history.json');

// ファイルを読み込む
fs.readFile(filePath, 'utf8', (err, data) => {
  if (err) {
    console.error('ファイルの読み込みに失敗しました:', err);
    return;
  }

  try {
    const jsonData = JSON.parse(data);
    
    // 最初の3頭にテストコメントを追加
    for (let i = 0; i < 3 && i < jsonData.horses.length; i++) {
      if (jsonData.horses[i].history && jsonData.horses[i].history.length > 0) {
        jsonData.horses[i].history[0].comment = testComments[i % testComments.length];
      }
    }

    // 更新日時を更新
    jsonData.metadata.last_updated = new Date().toISOString();
    jsonData.metadata.comment_added = true;

    // ファイルに書き戻す
    fs.writeFile(filePath, JSON.stringify(jsonData, null, 2), 'utf8', (err) => {
      if (err) {
        console.error('ファイルの書き込みに失敗しました:', err);
        return;
      }
      console.log('テストコメントを追加しました。');
    });
  } catch (err) {
    console.error('JSONのパースに失敗しました:', err);
  }
});
