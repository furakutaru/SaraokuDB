// オークションページで実行するスクリプト

// 馬のデータを抽出する関数
function extractHorseData() {
  // ページ内のスクリプトを検索
  const scripts = Array.from(document.getElementsByTagName('script'));
  let horseData = [];

  scripts.forEach(script => {
    const content = script.textContent;
    // 馬のデータを含むスクリプトを検索
    if (content.includes('topItemName')) {
      // 馬のデータを抽出する正規表現
      const regex = /\{itemId:(\d+),pdfUrl:"([^"]+)",topItemName:"([^"]+)",offererName:"([^"]*)",basicInfoUrl:"([^"]*)",movieUrl:([^,]+),image:"([^"]+)",(?:lastBreedingDate:"([^"]*)",sireName:"([^"]*)",mareUrl:"([^"]*)",birthday:"([^"]*)"|price:"([^"]*)",sex:([^,]+),\s*age:([^,}]+))/g;
      
      let match;
      while ((match = regex.exec(content)) !== null) {
        const horse = {
          id: match[1],
          pdfUrl: match[2],
          name: match[3],
          seller: match[4],
          jbisUrl: match[5],
          movieUrl: match[6],
          imageUrl: match[7],
          // 繁殖牝馬の情報
          lastBreedingDate: match[8],
          sireName: match[9],
          mareUrl: match[10],
          birthday: match[11],
          // 現役馬の情報
          price: match[12],
          sex: match[13],
          age: match[14]
        };
        horseData.push(horse);
      }
    }
  });

  return horseData;
}

// データを整形して表示する関数
function displayHorseData() {
  const data = extractHorseData();
  console.log('抽出した馬のデータ:', data);
  
  // 結果を表示するための要素を作成
  const resultsDiv = document.createElement('div');
  resultsDiv.style.padding = '20px';
  resultsDiv.style.backgroundColor = '#f5f5f5';
  resultsDiv.style.border = '1px solid #ccc';
  resultsDiv.style.marginTop = '20px';
  resultsDiv.style.maxHeight = '500px';
  resultsDiv.style.overflowY = 'auto';
  
  resultsDiv.innerHTML = `<h2>抽出結果 (${data.length}頭)</h2>`;
  
  data.forEach((horse, index) => {
    const horseDiv = document.createElement('div');
    horseDiv.style.borderBottom = '1px solid #ddd';
    horseDiv.style.padding = '10px';
    horseDiv.style.marginBottom = '10px';
    
    let html = `
      <h3>${index + 1}. ${horse.name}</h3>
      <p><strong>ID:</strong> ${horse.id}</p>
      <p><strong>売主:</strong> ${horse.seller}</p>
    `;
    
    if (horse.price) {
      html += `
        <p><strong>価格:</strong> ${horse.price}</p>
        <p><strong>性別:</strong> ${horse.sex}</p>
        <p><strong>年齢:</strong> ${horse.age}</p>
      `;
    } else if (horse.sireName) {
      html += `
        <p><strong>種牡馬:</strong> ${horse.sireName}</p>
        <p><strong>最終繁殖日:</strong> ${horse.lastBreedingDate}</p>
        <p><strong>生年月日:</strong> ${horse.birthday}</p>
      `;
    }
    
    html += `
      <p><strong>JBIS:</strong> <a href="${horse.jbisUrl}" target="_blank">${horse.jbisUrl}</a></p>
      <p><a href="${horse.pdfUrl}" target="_blank">PDFを見る</a></p>
    `;
    
    horseDiv.innerHTML = html;
    resultsDiv.appendChild(horseDiv);
  });
  
  // ページに結果を追加
  document.body.appendChild(resultsDiv);
  
  // 結果をコンソールにも出力
  console.log('CSV形式のデータ:');
  console.log('名前,性別,年齢,売主,価格,種牡馬,最終繁殖日,生年月日,JBIS URL');
  data.forEach(horse => {
    const row = [
      `"${horse.name}"`,
      horse.sex || '',
      horse.age || '',
      `"${horse.seller}"`,
      horse.price || '',
      `"${horse.sireName || ''}"`,
      horse.lastBreedingDate || '',
      horse.birthday || '',
      horse.jbisUrl
    ].join(',');
    console.log(row);
  });
  
  return data;
}

// ページの読み込みが完了したら実行
document.addEventListener('DOMContentLoaded', () => {
  // 5秒待ってから実行（動的読み込みを待つ）
  setTimeout(displayHorseData, 5000);
});

// ページにボタンを追加
const button = document.createElement('button');
button.textContent = '馬のデータを抽出';
button.style.position = 'fixed';
button.style.top = '10px';
button.style.right = '10px';
button.style.zIndex = '9999';
button.style.padding = '10px 20px';
button.style.backgroundColor = '#4CAF50';
button.style.color = 'white';
button.style.border = 'none';
button.style.borderRadius = '4px';
button.style.cursor = 'pointer';
button.onclick = displayHorseData;

document.body.appendChild(button);

console.log('馬データ抽出スクリプトを読み込みました。ページに「馬のデータを抽出」ボタンが表示されます。');
