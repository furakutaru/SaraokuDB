import sys
import os
import json
import time
import requests
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
import re
import requests

def test_prize_extraction(html_file):
    """HTMLファイルから賞金情報を抽出するテスト"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬のリスト要素を探す
    horse_elements = soup.select('div.auctionTableCard, div.auctionTableRow')
    
    for idx, element in enumerate(horse_elements[:2], 1):  # 最初の2頭のみテスト
        print(f"\n=== 馬 {idx}の情報 ===")
        
        # 馬名を抽出
        name_elem = element.select_one('.auctionTableCard__name, .horseName')
        name = name_elem.get_text(strip=True) if name_elem else '名前不明'
        print(f"馬名: {name}")
        
        # 賞金を抽出
        print("\n賞金抽出を開始...")
        
        # 1. まずはauctionTableCard__priceクラスを直接探す
        price_elem = element.select_one('.auctionTableCard__price .value')
        
        if price_elem:
            prize_text = price_elem.get_text(strip=True)
            print(f"賞金テキスト: {prize_text}")
            
            # 数値部分を抽出（例: "0.0万円" -> 0.0）
            match = re.search(r'([\d,\.]+)', prize_text)
            if match:
                try:
                    total_prize = float(match.group(1).replace(',', ''))
                    print(f"抽出した総賞金: {total_prize}万円")
                except ValueError as e:
                    print(f"賞金の数値変換エラー: {e}")
        else:
            print("警告: 賞金要素が見つかりませんでした")
        
        # 2. 他の価格関連要素を表示（デバッグ用）
        debug_price_elems = element.find_all('div', class_=lambda x: x and 'price' in str(x).lower())
        if debug_price_elems:
            print("\nデバッグ: その他の価格関連要素:")
            for i, elem in enumerate(debug_price_elems, 1):
                print(f"  {i}. クラス: {elem.get('class', [])}, テキスト: {elem.get_text(strip=True)}")
        
        print("-" * 50)

def normalize_jbis_url(jbis_url: str) -> str:
    """JBIS URLを基本情報ページのURLに正規化する"""
    if not jbis_url:
        return ""
    # 血統情報ページやレコードページを基本情報ページに変換
    return jbis_url.replace('/pedigree/', '/').replace('/record/', '/')

def extract_prize_from_jbis(jbis_url: str) -> float:
    """JBISページから総賞金を抽出する"""
    if not jbis_url:
        return None
        
    try:
        # URLを正規化
        normalized_url = normalize_jbis_url(jbis_url)
        if not normalized_url.startswith('http'):
            normalized_url = f'https://www.jbis.or.jp{normalized_url}'
            
        print(f"JBISページにアクセス中: {normalized_url}")
        response = requests.get(normalized_url, timeout=30)
        response.raise_for_status()
        
        # レスポンスのエンコーディングを明示的に指定
        response.encoding = 'utf-8'
        content = response.text
        
        # 不正な文字を削除
        content = content.encode('utf-8', 'ignore').decode('utf-8')
        
        soup = BeautifulSoup(content, 'html.parser')
        total_prize = None
        
        # 方法1: dtタグから総賞金を取得
        total_prize_dt = None
        for dt in soup.find_all('dt'):
            if dt.get_text(strip=True) == '総賞金':
                total_prize_dt = dt
                break
                
        if total_prize_dt and total_prize_dt.find_next_sibling('dd'):
            prize_text = total_prize_dt.find_next_sibling('dd').get_text(strip=True)
            match = re.search(r'([\d,]+(?:\.\d+)?)', prize_text)
            if match:
                total_prize = float(match.group(1).replace(',', ''))
                print(f"  dtタグから総賞金を取得: {total_prize}万円")
        
        # 方法2: 正規表現で直接検索（フォールバック）
        if total_prize is None:
            prize_match = re.search(r'総賞金\s*([\d,]+(?:\.\d+)?)\s*万円', content)
            if prize_match:
                total_prize = float(prize_match.group(1).replace(',', ''))
                print(f"  正規表現で総賞金を取得: {total_prize}万円")
        
        return total_prize
        
    except requests.exceptions.RequestException as e:
        print(f"  JBISへのリクエスト中にエラーが発生: {e}")
    except Exception as e:
        print(f"  JBISからの賞金取得中にエラーが発生: {str(e)}")
    
    return None

def save_to_processed_horses(horses: list, output_dir: str = 'data'):
    """馬の情報をprocessed_horses.jsonに保存する"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'processed_horses.json')
    
    # 既存のデータを読み込む（存在する場合）
    existing_data = {}
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
    
    # 新しいデータで更新
    for horse in horses:
        horse_id = horse.get('id')
        if horse_id is not None:
            if str(horse_id) not in existing_data:
                existing_data[str(horse_id)] = {}
            existing_data[str(horse_id)].update(horse)
    
    # 保存
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(existing_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n馬の情報を {output_path} に保存しました。")

def main():
    # キャッシュディレクトリのパス
    cache_dir = "/Users/yum.ishii/SaraokuDB/cache/20250818"
    output_file = os.path.join(cache_dir, "processed_horses.json")
    
    # リストページのHTMLを読み込む
    list_html_path = os.path.join(cache_dir, "list.html")
    if not os.path.exists(list_html_path):
        print(f"エラー: {list_html_path} が見つかりません。")
        return
    
    print(f"リストページを読み込み中: {list_html_path}")
    with open(list_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # スクレイピングを実行
    print("\nスクレイピングを開始します...")
    start_time = time.time()
    
    # リストページから馬の情報を取得
    soup = BeautifulSoup(html_content, 'html.parser')
    horses = []
    horse_elements = soup.select('div.auctionTableCard, div.auctionTableRow')
    
    for idx, element in enumerate(horse_elements, 1):
        try:
            print(f"\n=== 馬 {idx}/{len(horse_elements)} の処理を開始 ===")
            
            # 馬名を抽出
            name_elem = element.select_one('.auctionTableCard__name, .horseName')
            name = name_elem.get_text(strip=True) if name_elem else '名前不明'
            print(f"馬名: {name}")
            
            # 馬の基本情報を作成
            horse_data = {
                'name': name,
                'id': idx,
                'scraped_at': datetime.now().isoformat()
            }
            
            # 賞金を抽出
            price_elem = element.select_one('.auctionTableCard__price .value')
            if price_elem:
                prize_text = price_elem.get_text(strip=True)
                match = re.search(r'([\d,\.]+)', prize_text)
                if match:
                    try:
                        total_prize = float(match.group(1).replace(',', ''))
                        horse_data['total_prize_start'] = total_prize
                        print(f"リストページから総賞金を取得: {total_prize}万円")
                    except ValueError as e:
                        print(f"賞金の数値変換エラー: {e}")
            
            # 詳細ページのURLを抽出
            detail_url = ''
            link_selectors = [
                'a.auctionTableCard__name--link',
                'a[href*="item"]',
                'a[href*="/horse/"]',
                'a[href*="auction"]',
                'a[href*="detail"]'
            ]
            
            for selector in link_selectors:
                link_elem = element.select_one(selector)
                if link_elem and 'href' in link_elem.attrs:
                    detail_url = link_elem['href']
                    if not detail_url.startswith('http'):
                        detail_url = f"https://auction.keiba.rakuten.co.jp{detail_url}"
                    break
            
            if detail_url:
                horse_data['detail_url'] = detail_url
                
                # JBIS URLを抽出（詳細ページから取得）
                try:
                    # キャッシュから詳細ページを読み込む
                    horse_id = re.search(r'/horse/(\d+)', detail_url)
                    if horse_id:
                        detail_file = os.path.join(cache_dir, f"details/{horse_id.group(1)}.html")
                        if os.path.exists(detail_file):
                            with open(detail_file, 'r', encoding='utf-8') as f:
                                detail_html = f.read()
                            
                            # JBISリンクを抽出
                            detail_soup = BeautifulSoup(detail_html, 'html.parser')
                            jbis_link = detail_soup.find('a', href=lambda x: x and 'jbis.or.jp' in x)
                            if jbis_link:
                                jbis_url = jbis_link['href']
                                horse_data['jbis_url'] = jbis_url
                                print(f"JBIS URLを取得: {jbis_url}")
                                
                                # JBISから賞金情報を取得
                                try:
                                    normalized_jbis_url = jbis_url.replace('/pedigree/', '/').replace('/record/', '/')
                                    if normalized_jbis_url != jbis_url:
                                        print(f"JBIS URLを正規化: {jbis_url} -> {normalized_jbis_url}")
                                    
                                    # JBISページを取得
                                    jbis_response = requests.get(normalized_jbis_url, timeout=30)
                                    jbis_response.raise_for_status()
                                    jbis_soup = BeautifulSoup(jbis_response.content, 'html.parser')
                                    
                                    # 総賞金を抽出
                                    total_prize_latest = None
                                    
                                    # 方法1: dtタグから総賞金を取得
                                    total_prize_dt = jbis_soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                                    if total_prize_dt and total_prize_dt.find_next_sibling('dd'):
                                        prize_text = total_prize_dt.find_next_sibling('dd').get_text(strip=True)
                                        match = re.search(r'([\d,]+(?:\.\d+)?)', prize_text)
                                        if match:
                                            total_prize_latest = float(match.group(1).replace(',', ''))
                                            print(f"JBISから総賞金を取得: {total_prize_latest}万円")
                                    
                                    # 方法2: 正規表現で直接検索（フォールバック）
                                    if total_prize_latest is None:
                                        prize_match = re.search(r'総賞金\s*([\d,]+(?:\.\d+)?)\s*万円', jbis_response.text)
                                        if prize_match:
                                            total_prize_latest = float(prize_match.group(1).replace(',', ''))
                                            print(f"正規表現で総賞金を取得: {total_prize_latest}万円")
                                    
                                    if total_prize_latest is not None:
                                        horse_data['total_prize_latest'] = total_prize_latest
                                        print(f"total_prize_latestを{total_prize_latest}万円に設定")
                                    else:
                                        print("総賞金の取得に失敗しました")
                                    
                                except Exception as e:
                                    print(f"JBISからの賞金取得中にエラーが発生: {e}")
                
                except Exception as e:
                    print(f"詳細ページの処理中にエラーが発生: {e}")
            
            horses.append(horse_data)
            
            # サーバーに負荷をかけないように少し待機
            time.sleep(1)
            
        except Exception as e:
            print(f"馬 {idx} の処理中にエラーが発生: {e}")
            import traceback
            traceback.print_exc()
    
    # 結果をJSONファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(horses, f, ensure_ascii=False, indent=2)
    
    elapsed_time = time.time() - start_time
    print(f"\nスクレイピングが完了しました。結果を {output_file} に保存しました。")
    print(f"処理時間: {elapsed_time:.2f}秒")
    print(f"処理した馬の数: {len(horses)}")

if __name__ == "__main__":
    main()
