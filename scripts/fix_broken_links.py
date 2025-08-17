import re
from bs4 import BeautifulSoup

# キャッシュファイルのパス
list_page_path = '/Users/yum.ishii/SaraokuDB/scripts/test_cache/20250811_124216_a1a9f3e94be92e25f864231ea320699d.html'

# リストページを読み込む
with open(list_page_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# 壊れたリンクを修正する正規表現パターン
pattern = r'([a-zA-Z0-9_]+\.html)"\s+class="auctionTableCard__name'
replacement = r'" class="auctionTableCard__name'

# 正規表現で置換
fixed_content = re.sub(pattern, replacement, html_content)

# 変更を保存
with open(list_page_path, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print('壊れたリンクを修正しました。')
