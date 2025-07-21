import requests
from bs4 import BeautifulSoup

def debug_jbis_search():
    """JBISの検索機能をデバッグし、正しいリクエスト方法を特定する"""
    
    horse_name = "クレテイユ"  # 検索テスト用の馬名
    search_url = "https://www.jbis.or.jp/horse/"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print(f"=== JBIS検索デバッグ: '{horse_name}' ===")

    try:
        # 1. トップページにアクセスしてCookieを取得
        print("\n--- ステップ1: トップページアクセス ---")
        top_page_res = session.get(search_url, timeout=30)
        top_page_res.raise_for_status()
        print(f"ステータスコード: {top_page_res.status_code}")
        print(f"Cookie: {session.cookies.get_dict()}")

        # 2. 検索フォームのhiddenパラメータなどを探す
        soup = BeautifulSoup(top_page_res.content, 'html.parser')
        form = soup.find('form', id='form_search_horse_name')
        
        params = {}
        if form:
            hidden_tags = form.find_all('input', type='hidden')
            for tag in hidden_tags:
                params[tag.get('name')] = tag.get('value')
            print(f"フォームから取得したパラメータ: {params}")
        
        # 3. 検索を実行
        print(f"\n--- ステップ2: 検索実行 (POSTリクエスト) ---")
        # 検索キーワードを追加
        params['sname'] = horse_name
        
        # 検索リクエスト先のURLを特定 (formのaction属性)
        action_url = form.get('action') if form else 'https://www.jbis.or.jp/horse/list/'
        if not action_url.startswith('http'):
            action_url = "https://www.jbis.or.jp" + action_url

        print(f"検索URL: {action_url}")
        print(f"送信パラメータ: {params}")

        search_res = session.post(action_url, data=params, timeout=30)
        search_res.raise_for_status()

        print(f"ステータスコード: {search_res.status_code}")
        print(f"レスポンスURL: {search_res.url}")

        # 4. 結果ページのHTMLを保存・解析
        print("\n--- ステップ3: 結果ページの解析 ---")
        with open("debug_jbis.html", "w", encoding="utf-8") as f:
            f.write(search_res.text)
        print("結果を debug_jbis.html に保存しました。")
        
        result_soup = BeautifulSoup(search_res.content, 'html.parser')
        results_table = result_soup.find('table', class_='tbl-data-04')
        if results_table:
            print("✅ 検索結果テーブルが見つかりました。")
            rows = results_table.find_all('tr')
            print(f"検索結果: {len(rows) - 1}件")
        else:
            print("❌ 検索結果テーブルが見つかりませんでした。")

    except requests.exceptions.RequestException as e:
        print(f"\n❌ リクエストエラー: {e}")
    except Exception as e:
        print(f"\n❌ 予期せぬエラー: {e}")

if __name__ == "__main__":
    debug_jbis_search() 