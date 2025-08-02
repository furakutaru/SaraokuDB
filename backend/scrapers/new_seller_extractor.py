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

# テスト用のコード
if __name__ == "__main__":
    # テストケース1: 正規表現マッチ
    test1 = "販売申込者：テスト牧場（北海道）"
    result1 = _extract_seller(test1)
    print(f"テスト1 結果: {result1} (期待: テスト牧場)")
    
    # テストケース2: テーブルからの抽出
    test2 = """
    <table>
        <tr><th>販売申込者</th><td>テスト牧場（北海道）</td></tr>
    </table>
    """
    result2 = _extract_seller(test2)
    print(f"テスト2 結果: {result2} (期待: テスト牧場)")
    
    # テストケース3: 見つからない場合
    test3 = "テストデータ"
    result3 = _extract_seller(test3)
    print(f"テスト3 結果: '{result3}' (期待: '')")
