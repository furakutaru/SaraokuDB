import re
from bs4 import BeautifulSoup

def _extract_seller(page_text: str) -> str:
    """ページテキストから販売申込者を抽出する
    
    Args:
        page_text (str): 抽出元のページテキスト
        
    Returns:
        str: 抽出された販売申込者（見つからない場合は空文字列）
    """
    try:
        # 方法1: 正規表現で直接検索
        seller_match = re.search(r'販売申込者[：:]([^\n\r\t]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            # 「（」以降を削除して返す
            return re.sub(r'（.*$', '', seller).strip()
        
        # 方法2: テーブルから抽出
        soup = BeautifulSoup(page_text, 'html.parser')
        table_rows = soup.find_all('tr')
        for row in table_rows:
            th = row.find('th')
            td = row.find('td')
            if th and td and ('販売申込者' in th.get_text() or 'seller' in th.get_text().lower()):
                seller = td.get_text(strip=True)
                return re.sub(r'（.*$', '', seller).strip()
        
        return ''
        
    except Exception as e:
        print(f"販売申込者の抽出中にエラーが発生しました: {str(e)}")
        return ''
