import sys
import os
import logging

# スクリプトの親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# モジュールをインポート
try:
    # スクリプトが直接実行される場合
    from improved_scraper import ImprovedRakutenScraper
except ImportError:
    # スクリプトがモジュールとして実行される場合
    try:
        from scripts.improved_scraper import ImprovedRakutenScraper
    except ImportError as e:
        print(f"モジュールのインポートに失敗しました: {e}")
        sys.exit(1)

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルでログを出力
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper_debug.log', mode='w', encoding='utf-8')
    ]
)

# BeautifulSoupとurllib3のログレベルをWARNINGに設定して、デバッグログを減らす
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('bs4').setLevel(logging.WARNING)

def test_scraper():
    """スクレイパーのテストを実行"""
    try:
        print("スクレイパーを初期化中...")
        # 本番モードで実行（キャッシュなし）
        scraper = ImprovedRakutenScraper(use_cache=False)
        
        print("\n馬の一覧を取得中...")
        horses = scraper.scrape_horse_list()
        
        if not horses:
            print("エラー: 馬の情報を取得できませんでした")
            return False
            
        print(f"\n成功: {len(horses)}頭の馬情報を取得しました")
        
        # 最初の3頭の情報を表示
        print("\n=== 取得した馬の情報（最初の3頭）===")
        for i, horse in enumerate(horses[:3], 1):
            print(f"\n{i}. 馬名: {horse.get('name', 'N/A')}")
            print(f"   性別: {horse.get('sex', 'N/A')}, 年齢: {horse.get('age', 'N/A')}")
            print(f"   売主: {horse.get('seller', 'N/A')}")
            print(f"   URL: {horse.get('detail_url', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import sys
    
    # コマンドライン引数を確認
    if len(sys.argv) > 1 and sys.argv[1] == '--horse-id':
        # 特定の馬IDを指定して実行
        if len(sys.argv) < 3:
            print("エラー: 馬IDを指定してください")
            sys.exit(1)
            
        horse_id = sys.argv[2]
        print(f"=== 馬ID: {horse_id} の情報を取得します ===")
        if not scrape_specific_horse(horse_id):
            sys.exit(1)
    else:
        # 通常のテスト実行
        print("=== 楽天競馬オークション スクレイパーテスト ===")
        print("本番モードで実行します（キャッシュなし）\n")
        
        if test_scraper():
            print("\nスクレイピングが正常に完了しました")
{{ ... }}
            print("\nスクレイピング中にエラーが発生しました")
            sys.exit(1)
    else:
        print("\nテストが失敗しました。詳細はログファイルを確認してください。", file=sys.stderr)
        sys.exit(1)
