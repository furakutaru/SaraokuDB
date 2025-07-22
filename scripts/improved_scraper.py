#!/usr/bin/env python3
"""
改善されたスクレイピングスクリプト
seleniumを使わずにrequestsとBeautifulSoupで実装
正しいデータ抽出ロジックを含む
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from typing import List, Dict, Optional
from datetime import datetime

class ImprovedRakutenScraper:
    def __init__(self):
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        self.session = requests.Session()
        # ブラウザのように見せるためのヘッダー
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def get_auction_date(self) -> str:
        """ページから開催日を取得"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 開催日を探す（実際のサイト構造に合わせて調整）
            date_elements = soup.find_all(text=re.compile(r'\d{4}年\d{1,2}月\d{1,2}日'))
            if date_elements:
                date_text = date_elements[0].strip()
                # "2025年7月13日" → "2025-07-13"
                match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_text)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return datetime.now().strftime("%Y-%m-%d")
        except Exception as e:
            print(f"開催日の取得に失敗: {e}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def scrape_horse_list(self) -> List[Dict]:
        """トップページから馬のリストを取得"""
        horses = []
        
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 馬のリンクを探す
            horse_links = []
            
            # すべてのリンクをチェック
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href and '/item/' in href:
                    link_text = link.get_text(strip=True)
                    # 不要なリンクを除外
                    if (link_text and len(link_text) > 1 and 
                        '詳細血統表' not in link_text and 
                        '血統表' not in link_text and
                        '詳細' not in link_text):
                        if not href.startswith('http'):
                            href = self.base_url + href.lstrip('/')
                        horse_links.append({
                            'text': link_text,
                            'url': href
                        })
            
            print(f"馬のリンクを{len(horse_links)}個発見")
            
            # 各馬の詳細ページを取得
            for i, link in enumerate(horse_links):
                print(f"詳細情報を取得中... ({i+1}/{len(horse_links)}) {link['text']}")
                
                detail_data = self.scrape_horse_detail(link['url'])
                if detail_data and detail_data.get('name'):  # 名前が取得できた場合のみ追加
                    detail_data['name'] = link['text']
                    detail_data['detail_url'] = link['url']
                    horses.append(detail_data)
                
                time.sleep(1)  # サーバーに負荷をかけないよう待機
                        
        except Exception as e:
            print(f"馬リストの取得に失敗: {e}")
            
        return horses
    
    def scrape_horse_detail(self, detail_url: str) -> Optional[Dict]:
        """個別ページから詳細情報を取得"""
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            detail_data = {}
            
            # 馬名、性別、年齢
            detail_data.update(self._extract_name_sex_age(page_text))
            
            # 落札価格（税込価格を取得）
            detail_data['sold_price'] = self._extract_sold_price(page_text)
            
            # 血統情報
            detail_data.update(self._extract_pedigree(page_text))
            
            # 馬体重
            detail_data['weight'] = self._extract_weight(page_text)
            
            # 成績
            detail_data['race_record'] = self._extract_race_record(page_text)
            
            # 獲得賞金
            detail_data.update(self._extract_prize_money(page_text))
            
            # コメント
            detail_data['comment'] = self._extract_comment(page_text)
            
            # 疾病タグ
            detail_data['disease_tags'] = self._extract_disease_tags(detail_data.get('comment', ''))
            
            # 馬体画像
            detail_data['primary_image'] = self._extract_primary_image(soup)
            
            # 販売申込者
            detail_data['seller'] = self._extract_seller(page_text)
            
            return detail_data
            
        except Exception as e:
            print(f"詳細情報の取得に失敗: {e}")
            return None
    
    def _extract_name_sex_age(self, page_text: str) -> Dict:
        """馬名、性別、年齢を解析"""
        result = {}
        
        # 馬名、性別、年齢のパターンを探す
        # 例: "クレテイユ　　牡５歳"
        name_pattern = r'([^\s　]+)\s*[　\s]+([牡牝セ])\s*(\d+)歳'
        match = re.search(name_pattern, page_text)
        
        if match:
            result['name'] = match.group(1)
            result['sex'] = match.group(2)
            result['age'] = int(match.group(3))
        
        return result
    
    def _extract_sold_price(self, page_text: str) -> str:
        """落札価格を抽出（税込価格）"""
        # 現在価格の税込価格を取得（例: "2,000,000円(税込 2,200,000円)"）
        price_match = re.search(r'(\d{1,3}(?:,\d{3})*)円\(税込\s*(\d{1,3}(?:,\d{3})*)円\)', page_text)
        if price_match:
            # 税込価格を使用
            return price_match.group(2).replace(',', '')
        
        # フォールバック: 単純な税込価格パターン
        price_match = re.search(r'税込\s*(\d{1,3}(?:,\d{3})*)円', page_text)
        if price_match:
            return price_match.group(1).replace(',', '')
        
        return ''
    
    def _extract_pedigree(self, page_text: str) -> Dict:
        """血統情報を抽出"""
        result = {}
        
        # 父
        sire_match = re.search(r'父[：:]\s*([^\n]+)', page_text)
        if sire_match:
            result['sire'] = sire_match.group(1).strip()
        
        # 母
        dam_match = re.search(r'母[：:]\s*([^\n]+)', page_text)
        if dam_match:
            result['dam'] = dam_match.group(1).strip()
        
        # 母父
        dam_sire_match = re.search(r'母の父[：:]\s*([^\n]+)', page_text)
        if dam_sire_match:
            result['dam_sire'] = dam_sire_match.group(1).strip()
        
        return result
    
    def _extract_weight(self, page_text: str) -> Optional[int]:
        """馬体重を抽出"""
        # "最終出走馬体重：XXXkg" を探す
        match = re.search(r'最終出走馬体重[：:]\s*(\d+)kg', page_text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_race_record(self, page_text: str) -> str:
        """成績を抽出"""
        # "通算成績：24戦4勝［4-6-2-12］" を探す
        match = re.search(r'通算成績[：:]\s*(\d+戦\d+勝［\d+-\d+-\d+-\d+］)', page_text)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_prize_money(self, page_text: str) -> Dict:
        result = {}
        # 中央・地方・総獲得賞金の全パターンをカバー
        central_prize_match = re.search(r'中央獲得賞金[：:]\s*([\d,.]+)万?円', page_text)
        local_prize_match = re.search(r'地方獲得賞金[：:]\s*([\d,.]+)万?円', page_text)
        total_prize_match = re.search(r'総獲得賞金[：:]\s*([\d,.]+)万?円', page_text)
        total_prize = 0.0 # デフォルトを0.0に
        try:
            if total_prize_match:
                total_prize = float(total_prize_match.group(1).replace(',', ''))
            else:
                central = float(central_prize_match.group(1).replace(',', '')) if central_prize_match else 0.0
                local = float(local_prize_match.group(1).replace(',', '')) if local_prize_match else 0.0
                total_prize = central + local
        except (ValueError, TypeError):
             total_prize = 0.0 # 変換失敗時も0.0に
        result['total_prize_start'] = total_prize
        result['total_prize_latest'] = total_prize
        return result
    
    def _extract_comment(self, page_text: str) -> str:
        """コメントを抽出"""
        # "本馬について" の後のテキストを探す
        comment_match = re.search(r'本馬について(.+?)(?=\n\n|\n販売申込者|$)', page_text, re.DOTALL)
        if comment_match:
            return comment_match.group(1).strip()
        return ""
    
    def _extract_disease_tags(self, comment: str) -> str:
        """疾病タグを抽出"""
        disease_keywords = [
            '喉頭片麻痺', '喘鳴症', '脚部不安', '関節炎', '腱炎',
            '骨折', '脱臼', '筋肉痛', '腰痛', '腹痛', '球節炎', 'さく癖'
        ]
        
        found_diseases = []
        for disease in disease_keywords:
            if disease in comment:
                found_diseases.append(disease)
        
        return ','.join(found_diseases) if found_diseases else "なし"
    
    def _extract_primary_image(self, soup) -> str:
        """馬体画像のURLを抽出"""
        try:
            # 画像要素を探す
            image_elements = soup.find_all('img')
            for img in image_elements:
                src = img.get('src', '')
                if src and isinstance(src, str) and 'horse' in src.lower() and ('jpg' in src.lower() or 'jpeg' in src.lower() or 'png' in src.lower()):
                    return src
            
            return ""
        except Exception as e:
            print(f"馬体画像の抽出に失敗: {e}")
            return ""
    
    def _extract_seller(self, page_text: str) -> str:
        """販売申込者を抽出"""
        seller_match = re.search(r'販売申込者[：:]\s*([^\n]+)', page_text)
        if seller_match:
            return seller_match.group(1).strip()
        return ""
    
    def scrape_all_horses(self, auction_date: str = None) -> List[Dict]:
        """全馬の情報を取得"""
        if not auction_date:
            auction_date = self.get_auction_date()
        
        print(f"オークション日: {auction_date}")
        
        # 馬のリストを取得
        horses = self.scrape_horse_list()
        print(f"{len(horses)}頭の馬を発見しました。")
        
        # オークション日を追加
        for horse in horses:
            horse['auction_date'] = auction_date
        
        return horses

def scrape_from_history_urls():
    """horses_history.jsonのURLリストからスクレイピングする"""
    import os
    import json
    print(f"DEBUG: using json module: {json.__file__}")

    input_file = "/tmp/history_44.json"
    output_file = "/tmp/scraped_result.json"
    
    if not os.path.exists(input_file):
        print(f"ERROR: {input_file} が見つかりません")
        return

    data = None
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR: failed to load or parse {input_file}: {e}")
        return

    if not data:
        print(f"ERROR: No data loaded from {input_file}")
        return

    # horses_list = data # 'horses' キーがトップレベルにある場合
    horses_list = data.get("horses", [])

    url_list = []
    missing_url_horses = []
    for horse_data in horses_list:
        top_level_url = horse_data.get("detail_url")
        history_url = None
        if horse_data.get("history"):
            # historyの最初の要素からURLを取得しようと試みる
            history_entry = horse_data["history"][0] if horse_data["history"] else {}
            history_url = history_entry.get("detail_url")

        final_url = top_level_url or history_url

        if final_url:
            url_list.append(final_url)
        else:
            horse_name = "名前不明"
            if horse_data.get("history") and horse_data["history"]:
                horse_name = horse_data["history"][0].get("name", horse_name)
            elif "name" in horse_data:
                horse_name = horse_data["name"]
            
            missing_url_horses.append(horse_name)

    # 重複を除去
    url_list = sorted(list(set(url_list)))

    print(f"履歴ファイルから{len(url_list)}件のURLを再取得します")
    if missing_url_horses:
        print(f"--- URL欠損データ ({len(missing_url_horses)}件) ---")
        for name in sorted(list(set(missing_url_horses))):
            print(f"- {name}")
        print("------------------------------------")
        # URL欠損がある場合は、ここで処理を中断または補完ロジックへ
        # return

    scraper = ImprovedRakutenScraper()
    horses = []
    failed = []
    for i, url in enumerate(url_list, 1):
        print(f"({i}/{len(url_list)}) {url}")
        try:
            horse = scraper.scrape_horse_detail(url)
            if horse:
                horse["detail_url"] = url
                horses.append(horse)
            else:
                failed.append({"url": url, "reason": "no data returned"})
        except Exception as e:
            failed.append({"url": url, "reason": str(e)})
        time.sleep(1)
    
    # メタデータ
    total_horses = len(horses)
    def to_num(x):
        try:
            return float(x)
        except Exception:
            return 0
    avg_price = sum(to_num(h.get('sold_price', 0)) for h in horses) / total_horses if total_horses > 0 else 0
    out_data = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "total_horses": total_horses,
            "average_price": int(avg_price),
        },
        "horses": horses,
        "failed": failed
    }
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)
    print(f"{total_horses}頭分のデータを {output_file} に保存しました")
    if failed:
        print(f"取得失敗: {len(failed)}件")
        for fitem in failed:
            print(f"FAILED: {fitem['url']} - {fitem['reason']}")

def main():
    """メイン実行関数"""
    # scraper = ImprovedRakutenScraper()
    # horses = scraper.scrape_all_horses()
    
    # if horses:
    #     # 結果をJSONファイルに保存
    #     output_file = "scraped_horses.json"
    #     with open(output_file, 'w', encoding='utf-8') as f:
    #         json.dump(horses, f, ensure_ascii=False, indent=2)
        
    #     print(f"\n{len(horses)}頭の馬のデータを {output_file} に保存しました")
        
    #     # 各馬の情報を表示
    #     for i, horse in enumerate(horses, 1):
    #         print(f"\n{i}. {horse.get('name', 'N/A')}")
    #         print(f"   落札価格: {horse.get('sold_price', '')}")
    #         print(f"   賞金: {horse.get('total_prize_start', '')}")
    #         print(f"   成績: {horse.get('race_record', 'N/A')}")
    # else:
    #     print("馬のデータを取得できませんでした")
    pass # 何もしない

if __name__ == "__main__":
    scrape_from_history_urls() 