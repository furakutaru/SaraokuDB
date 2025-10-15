def fix_indent():
    # ファイルを読み込む
    with open('/Users/yum.ishii/SaraokuDB/scripts/improved_scraper.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 1265行目（0ベースでは1264行目）のインデントを修正
    if len(lines) > 1264:
        # 現在の行を取得
        line = lines[1264]
        # 先頭の空白を削除
        lines[1264] = line.lstrip()
        
        # ファイルに書き戻す
        with open('/Users/yum.ishii/SaraokuDB/scripts/improved_scraper.py', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("インデントを修正しました。")
    else:
        print("ファイルの行数が足りません。")

if __name__ == "__main__":
    fix_indent()
