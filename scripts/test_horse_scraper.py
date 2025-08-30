import os
import sys
import logging
import time
from datetime import datetime
from bs4 import BeautifulSoup

# Add the parent directory to the path so we can import the scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the scraper and config classes
from improved_scraper import ImprovedRakutenScraper, ScraperConfig, TestConfig

# Create a test configuration
TEST_CONFIG = TestConfig(
    use_cache=False,  # Disable cache for testing
    cache_dir='test_cache',
    max_workers=1  # Use 1 worker for testing
)

# Set additional test-specific configurations
TEST_CONFIG.base_url = 'https://auction.keiba.rakuten.co.jp/'
TEST_CONFIG.timeout = 30
TEST_CONFIG.debug = True
TEST_CONFIG.output_dir = 'test_output'
TEST_CONFIG.html_dump_dir = 'test_html_dump'

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_scraper.log')
    ]
)

def test_scraper_with_sample_html():
    """Test the scraper with a sample HTML file."""
    import os
    # Create a test HTML file
    sample_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Horse List</title>
    </head>
    <body>
        <div class="horse-card">
            <div class="horse-name">テスト馬1</div>
            <div class="sex-age">牡3</div>
            <div class="sire">テスト父1</div>
            <div class="dam">テスト母1</div>
            <div class="damsire">テスト母父1</div>
            <div class="seller">テスト牧場1</div>
            <a href="/detail/1">詳細を見る</a>
        </div>
        <div class="horse-card">
            <div class="horse-name">テスト馬2</div>
            <div class="sex-age">牝2</div>
            <div class="sire">テスト父2</div>
            <div class="dam">テスト母2</div>
            <div class="damsire">テスト母父2</div>
            <div class="seller">テスト牧場2</div>
            <a href="/detail/2">詳細を見る</a>
        </div>
        <div class="horse-card">
            <div class="horse-name">テスト馬3</div>
            <div class="sex-age">セ4</div>
            <div class="sire">テスト父3</div>
            <div class="dam">テスト母3</div>
            <div class="damsire">テスト母父3</div>
            <div class="seller">テスト牧場3</div>
            <a href="/detail/3">詳細を見る</a>
        </div>
    </body>
    </html>
    """
    
    # Save the sample HTML to a file
    os.makedirs('test_html', exist_ok=True)
    html_file = 'test_html/horse_list.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(sample_html)
    
    # Create test directories
    os.makedirs('test_output', exist_ok=True)
    os.makedirs('test_cache', exist_ok=True)
    os.makedirs('test_html_dump', exist_ok=True)
    
    # Create the scraper with the test config
    scraper = ImprovedRakutenScraper(config=TEST_CONFIG)
    
    # Test with the sample HTML file
    print("\n=== テストモードで実行中 ===")
    test_horses = scraper.scrape_horse_list()
    print("\nテストモードの結果:")
    for i, horse in enumerate(test_horses, 1):
        print(f"{i}. {horse['name']} ({horse['sex']}{horse['age']}): {horse['seller']}")
    
    # Test with the sample HTML file as a file path
    print("\n=== サンプルHTMLファイルでテスト中 ===")
    try:
        file_horses = scraper.scrape_horse_list(html_file)
        if not file_horses:
            print("警告: 馬のデータが抽出できませんでした")
        else:
            print("\nサンプルHTMLファイルの結果:")
            for i, horse in enumerate(file_horses, 1):
                name = horse.get('name', '')
                print(f"{i}. 馬名: {name} (長さ: {len(name)}文字)")
                print(f"   性別: {horse.get('sex', '?')}, 年齢: {horse.get('age', '?')}, 販売者: {horse.get('seller', '不明')}")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    # 実際のウェブサイトからデータを取得してテスト
    print("\n=== 実際のウェブサイトからデータを取得中... ===")
    try:
        # テストモードを無効にして実際のウェブサイトからデータを取得
        scraper.test_mode = False
        print("テストモードを無効にしました")
        
        # ベースURLを更新
        scraper.base_url = "https://auction.keiba.rakuten.co.jp"
        print(f"ベースURLを設定しました: {scraper.base_url}")
        
        # トップページにアクセス
        print("\nトップページにアクセス中...")
        response = scraper.session.get(scraper.base_url, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"リダイレクト先: {response.url if response.history else 'リダイレクトなし'}")
        
        # HTMLをファイルに保存して確認
        import os
        os.makedirs('debug_html', exist_ok=True)
        with open('debug_html/auction_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("\nページのHTMLを debug_html/auction_page.html に保存しました")
        
        # ページの構造を確認
        print("\nページの構造を確認中...")
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 馬のリストを探す
        horse_elements = soup.find_all('a', href=lambda x: x and '/item/' in x)
        print(f"\n馬のリンクを {len(horse_elements)} 件見つけました")
        
        # 最初の数件のリンクを表示
        for i, elem in enumerate(horse_elements[:5], 1):
            print(f"{i}. {elem.get('href')} - {elem.get_text(strip=True, separator=' ')[:50]}...")
        
        # トップページから馬の一覧を取得
        print("\n馬の一覧を取得中...")
        real_horses = scraper.scrape_horse_list()
        
        if not real_horses:
            print("警告: 馬のデータを取得できませんでした")
        else:
            print(f"\n取得した馬の数: {len(real_horses)}頭")
            print("\n最初の5頭の馬の情報:")
            for i, horse in enumerate(real_horses[:5], 1):
                name = horse.get('name', '')
                print(f"{i}. 馬名: {name} (長さ: {len(name)}文字)")
                print(f"   性別: {horse.get('sex', '?')}, 年齢: {horse.get('age', '?')}, 販売者: {horse.get('seller', '不明')}")
                
                # 馬名が省略されていないか確認
                if '...' in name:
                    print("  警告: 馬名が省略されています！")
                elif len(name) >= 15:  # 長い名前の場合（適宜調整）
                    print(f"  情報: 長い馬名が検出されました ({len(name)}文字)")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # テストモードに戻す
        scraper.test_mode = True
    
    # Clean up
    if os.path.exists(html_file):
        os.remove(html_file)
    if os.path.exists('test_html') and not os.listdir('test_html'):
        os.rmdir('test_html')

def analyze_website_structure():
    """Analyze the structure of the Rakuten Keiba auction website."""
    import requests
    from bs4 import BeautifulSoup
    
    print("\n=== 楽天競馬オークションサイトの構造を分析中... ===")
    
    # セッションを作成
    session = requests.Session()
    
    # User-Agentを設定
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8'
    }
    
    # トップページにアクセス
    base_url = 'https://auction.keiba.rakuten.co.jp/'
    print(f"\nトップページにアクセス中: {base_url}")
    
    try:
        response = session.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # HTMLをファイルに保存
        os.makedirs('debug_html', exist_ok=True)
        with open('debug_html/auction_page.html', 'w', encoding='utf-8') as f:
            f.write(response.text)
        print("ページのHTMLを debug_html/auction_page.html に保存しました")
        
        # HTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 馬のリンクを探す
        horse_links = soup.find_all('a', href=lambda x: x and '/item/' in x)
        print(f"\n馬の詳細ページへのリンクを {len(horse_links)} 件見つけました")
        
        if horse_links:
            print("\n最初の5件の馬のリンク:")
            for i, link in enumerate(horse_links[:5], 1):
                print(f"{i}. {link.get('href')} - {link.get_text(strip=True, separator=' ')[:50]}...")
        
        # 馬のカードを探す
        horse_cards = soup.find_all('div', class_=lambda x: x and 'horse-card' in x.lower())
        print(f"\n馬のカードを {len(horse_cards)} 件見つけました")
        
        if horse_cards:
            print("\n最初の馬のカードのHTML構造:")
            print(str(horse_cards[0])[:500] + "...")
        
        # 馬の名前を探す
        horse_names = soup.find_all(['div', 'span'], class_=lambda x: x and 'name' in x.lower())
        print(f"\n馬の名前要素を {len(horse_names)} 件見つけました")
        
        if horse_names:
            print("\n最初の5件の馬の名前:")
            for i, name in enumerate(horse_names[:5], 1):
                print(f"{i}. {name.get_text(strip=True, separator=' ')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_scraper_with_actual_website():
    """Test the scraper with the actual Rakuten Keiba auction website."""
    print("\n=== 実際のウェブサイトでスクレイパーをテスト中... ===")
    
    # スクレイパーを初期化（テストモードはオフ）
    config = TestConfig(
        use_cache=True,  # 開発中はキャッシュを有効に
        cache_dir='test_cache',
        max_workers=1
    )
    
    # ベースURLを設定
    config.base_url = 'https://auction.keiba.rakuten.co.jp/'
    
    # スクレイパーを初期化
    scraper = ImprovedRakutenScraper(config)
    
    # テストモードを無効化
    scraper.test_mode = False
    
    try:
        # 馬の一覧を取得
        print("\n馬の一覧を取得中...")
        horses = scraper.scrape_horse_list()
        
        if not horses:
            print("警告: 馬のデータを取得できませんでした")
            return False
        
        print(f"\n取得した馬の数: {len(horses)}頭")
        
        # 最初の5頭の情報を表示
        print("\n最初の5頭の馬の情報:")
        for i, horse in enumerate(horses[:5], 1):
            print(f"{i}. {horse.get('name', 'N/A')} ({horse.get('sex', 'N/A')}{horse.get('age', 'N/A')})")
            print(f"   販売者: {horse.get('seller', 'N/A')}")
            print(f"   詳細URL: {horse.get('detail_url', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # まずはサンプルHTMLでテスト
    print("=== サンプルHTMLでのテストを開始します ===")
    test_scraper_with_sample_html()
    
    # 次に実際のウェブサイトの構造を分析
    print("\n" + "="*50)
    print("=== 実際のウェブサイトの構造を分析します ===")
    if analyze_website_structure():
        # 構造の分析が成功したら、実際のウェブサイトでテスト
        print("\n" + "="*50)
        test_scraper_with_actual_website()
