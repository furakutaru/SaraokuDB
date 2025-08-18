import os
import re
from pathlib import Path

def fix_horse_names(cache_dir):
    # 修正する馬名のマッピング
    name_mappings = {
        "ウィットビーアビ...": "ウィットビーアビー",
        "ドゥフトブリュー...": "ドゥフトブリューテ"
    }
    
    # キャッシュディレクトリ内の全HTMLファイルを取得
    cache_path = Path(cache_dir)
    html_files = list(cache_path.glob("**/*.html"))
    
    # 各HTMLファイルを処理
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 省略された馬名が含まれているか確認
            modified = False
            for old_name, new_name in name_mappings.items():
                if old_name in content:
                    content = content.replace(old_name, new_name)
                    modified = True
            
            # 変更があった場合はファイルを上書き
            if modified:
                with open(html_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"更新しました: {html_file}")
                
        except Exception as e:
            print(f"エラーが発生しました {html_file}: {str(e)}")

if __name__ == "__main__":
    # キャッシュディレクトリを指定
    cache_dir = "/Users/yum.ishii/SaraokuDB/cache"
    print("馬名の修正を開始します...")
    fix_horse_names(cache_dir)
    print("処理が完了しました。")
