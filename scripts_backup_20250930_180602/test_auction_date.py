from bs4 import BeautifulSoup
import re
from datetime import datetime
import logging

# テスト用のHTML
html = '''
<div class="subData">
    <div class="subData__item">
        <span class="subData__label">開始時間</span>
        <div class="subData__value">2023年12月31日(日) 12:00〜</div>
    </div>
</div>
'''

# BeautifulSoupオブジェクトを作成
soup = BeautifulSoup(html, 'html.parser')

# 開始時間ラベルを探す
start_time_label = soup.find('span', class_='subData__label', string=lambda text: text and '開始時間' in str(text))

if start_time_label:
    # 親要素を取得
    parent = start_time_label.find_parent()
    if parent:
        # 同じ親要素内のsubData__valueクラスを持つ要素を探す
        value_div = parent.find('div', class_='subData__value')
        if value_div:
            date_text = value_div.get_text(strip=True)
            # YYYY年MM月DD日形式の日付を探す
            match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_text)
            if match:
                year, month, day = match.groups()
                print(f"Extracted date: {year}-{int(month):02d}-{int(day):02d}")
            else:
                print("No date found in the text")
        else:
            print("No value div found")
    else:
        print("No parent found")
else:
    print("Start time label not found")
