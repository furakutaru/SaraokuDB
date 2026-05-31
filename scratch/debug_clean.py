import re
import unicodedata

def clean_name_text(raw_name: str) -> str:
    if not raw_name:
        return ""

    name = unicodedata.normalize("NFKC", str(raw_name))
    print(f"[1. Normalized] '{name}'")
    name = name.strip().replace('\n', ' ')
    patterns = [
        r'※.*$', r'登録抹消.*$', r'新馬.*$', r'未出走.*$',
        # Allow '当' as age prefix/value before '歳'
        r'\s+(?:セン|[牡牝セ])\s*(?:\d+|当)?\s*(?:歳|年)?',
        r'\(.*\)', r'\[.*\]'
    ]
    for pattern in patterns:
        name = re.sub(pattern, '', name)
        print(f"[2. Sub {pattern}] '{name}'")

    name = re.sub(r'\s+', ' ', name).strip()
    print(f"[3. Space sub] '{name}'")

    if name.endswith(' セン'):
        name = name[:-2].strip()
        print(f"[4. endswith ' セン'] '{name}'")

    return name

print("--- Test 1 ---")
clean_name_text("ウインアルバローズ　　牡７　　※地方競馬　在籍")
print("\n--- Test 2 ---")
clean_name_text("アレピアード　　セン６　　※地方競馬　在籍")
print("\n--- Test 3 ---")
clean_name_text("テートモダン　　セン４歳　　※地方競馬　在籍")
print("\n--- Test 4 ---")
clean_name_text("ボナデアの24　　牡当歳　　※育成馬（育成中の当歳馬）")
print("\n--- Test 5 ---")
clean_name_text("ヘキレキイッセン　　牡５歳　　※中央競馬　登録抹消")
