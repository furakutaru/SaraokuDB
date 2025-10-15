from pathlib import Path
import requests
from core.utils.html_saver import HTMLSaver

def main():
    print("HTMLSaverのテストを開始します...")
    
    # 保存先ディレクトリを設定
    save_dir = Path('test_html_output')
    
    # HTMLSaverを初期化
    html_saver = HTMLSaver(save_dir)
    print(f"HTML保存先: {save_dir.absolute()}")
    
    # テスト用のURLにアクセス
    test_url = "https://keiba.rakuten.co.jp/"
    print(f"テストURLにアクセス中: {test_url}")
    
    try:
        # テスト用のHTMLを取得
        response = requests.get(test_url)
        response.raise_for_status()
        html_content = response.text
        
        # HTMLを保存
        saved_path = html_saver.save(test_url, html_content)
        
        if saved_path:
            print(f"HTMLを保存しました: {saved_path}")
        else:
            print("HTMLの保存に失敗しました")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")

    print("\nテストが完了しました")

if __name__ == "__main__":
    main()
