import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union, cast
from datetime import datetime
try:
    from backend.scrapers.netkeiba_scraper import NetkeibaScraper
except ImportError:
    try:
        from .netkeiba_scraper import NetkeibaScraper
    except ImportError:
        from netkeiba_scraper import NetkeibaScraper

class RakutenAuctionScraper:
    def __init__(self):
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.netkeiba_scraper = NetkeibaScraper()
        
    def get_auction_date(self) -> str:
        """ページから開催日を取得"""
        try:
            return datetime.now().strftime("%Y-%m-%d")
        except Exception as e:
            print(f"開催日の取得に失敗: {e}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def scrape_horse_list(self) -> List[Dict]:
        """
        トップページから馬のリスト（馬名・総賞金・詳細URL）を取得
        """
        horses = []
        try:
            print("トップページにアクセス中...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # auctionTableCardクラスのdivを全て取得
            cards = soup.find_all('div', class_='auctionTableCard')
            for card in cards:
                # 馬名・詳細リンク
                name_elem = card.find('div', class_='auctionTableCard__name')
                if not name_elem:
                    continue
                a_tag = name_elem.find('a', href=True)
                if not a_tag:
                    continue
                horse_name = a_tag.get('title') or a_tag.get_text(strip=True) or ''
                detail_url = a_tag.get('href') or ''
                if not detail_url:
                    continue
                if not detail_url.startswith('http'):
                    detail_url = self.base_url.rstrip('/') + detail_url
                # 総賞金
                prize = ''
                total_prize_float = 0.0
                prize_elem = card.find('div', class_='auctionTableCard__price')
                if prize_elem:
                    label_elem = prize_elem.find('div', class_='label')
                    value_elem = prize_elem.find('div', class_='value')
                    if label_elem and value_elem and '総賞金' in label_elem.get_text():
                        prize = value_elem.get_text(strip=True)
                        try:
                            total_prize_float = float(prize.replace('万円', '').replace(',', ''))
                        except Exception:
                            total_prize_float = 0.0
                horses.append({
                    'name': horse_name,
                    'detail_url': detail_url,
                    'prize': prize,
                    'total_prize_start': total_prize_float,
                    'total_prize_latest': total_prize_float
                })
            print(f"{len(horses)}頭の馬を発見しました。")
            if len(horses) == 0:
                raise RuntimeError("馬リストが1頭も取得できませんでした。HTML構造やクラス名を再確認してください。")
        except Exception as e:
            print(f"馬リストの取得に失敗: {e}")
        return horses
    
    def _extract_horse_basic_info(self, card) -> Optional[Dict]:
        """馬カードから基本情報を抽出"""
        try:
            # 馬名とリンク
            name_element = card.find(class_="auctionTableCard__name")
            if name_element:
                name_link = name_element.find('a')
                if name_link:
                    # title属性があれば優先
                    horse_name = name_link.get('title') or name_link.get_text(strip=True)
                    detail_url = name_link.get('href')
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = self.base_url + detail_url
                else:
                    return None
            else:
                return None
            
            # 総賞金（万円単位）
            price_element = card.find(class_="auctionTableCard__price")
            total_prize = 0
            if price_element:
                value_element = price_element.find(class_="value")
                if value_element:
                    price_text = value_element.get_text(strip=True)
                    # "72.0万円" から数値を抽出（万円単位で保存）
                    match = re.search(r'(\d+\.?\d*)', price_text)
                    if match:
                        total_prize = float(match.group(1))  # 万円単位で保存
            
            # 販売申込者
            seller_element = card.find(class_="auctionTableCard__seller")
            seller = ""
            if seller_element:
                value_element = seller_element.find(class_="value")
                if value_element:
                    seller = value_element.get_text(strip=True)
            
            # 性別と年齢
            sex_age_element = card.find(class_="horseLabelWrapper")
            sex = ""
            age = 0
            if sex_age_element:
                sex_element = sex_age_element.find(class_="horseLabelWrapper__horseSex")
                age_element = sex_age_element.find(class_="horseLabelWrapper__horseAge")
                
                if sex_element:
                    sex = sex_element.get_text(strip=True)
                if age_element:
                    age_text = age_element.get_text(strip=True)
                    age_match = re.search(r'(\d+)', age_text)
                    if age_match:
                        age = int(age_match.group(1))
            
            return {
                'name': horse_name,
                'detail_url': detail_url,
                'total_prize_start': total_prize,
                'total_prize_latest': total_prize,
                'seller': seller,
                'sex': sex,
                'age': age
            }
            
        except Exception as e:
            print(f"基本情報の抽出に失敗: {e}")
            return None
    
    def scrape_horse_detail(self, detail_url: str) -> Optional[Dict]:
        """個別ページから詳細情報を取得"""
        try:
            print(f"詳細ページにアクセス中: {detail_url}")
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            detail_data = {}

            # 馬名（h1.itemDetail__title or titleタグ）
            name_tag = soup.find('h1', class_='itemDetail__title')
            full_name = name_tag.get_text(strip=True) if name_tag and name_tag.get_text() is not None else ''
            if not full_name:
                title_tag = soup.find('title')
                if title_tag and title_tag.get_text() is not None:
                    full_name = title_tag.get_text(strip=True)
            name_match = re.match(r'^([\w\-ァ-ヶ一-龠ぁ-んＡ-Ｚａ-ｚA-Za-z0-9]+)', full_name)
            horse_name = name_match.group(1) if name_match else full_name.split()[0]
            if not horse_name:
                print(f"[異常] 馬名が抽出できません: {detail_url}")
            detail_data['name'] = horse_name

            # --- JBISリンク抽出を追加 ---
            jbis_url = ''
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href:
                    # /record/が付いている場合は除去して基本情報ページのURLを作成
                    if '/record/' in href:
                        basic_info_url = href.replace('/record/', '')
                        if not basic_info_url.endswith('/'):
                            basic_info_url += '/'
                        jbis_url = basic_info_url
                    else:
                        jbis_url = href
                    break
            detail_data['jbis_url'] = jbis_url
            # --- ここまで追加 ---

            # 馬齢（「○歳」や「牡/牝○歳」パターン）
            page_text = soup.get_text() or ''
            age = ''
            age_match = re.search(r'([0-9]{1,2})歳', page_text)
            if age_match:
                age = age_match.group(1)
            detail_data['age'] = age
            if not age:
                print(f"[異常] 馬齢が抽出できません: {detail_url}")

            # 性別（「牡」「牝」「セン」パターン）
            sex = ''
            # タイトルやh1タグから必ず抽出
            title_text = ''
            if name_tag and name_tag.get_text() is not None:
                title_text = name_tag.get_text().strip()
            else:
                title_tag = soup.find('title')
                if title_tag and title_tag.get_text() is not None:
                    title_text = title_tag.get_text().strip()
            sex_match = re.match(r'^.+?[ \t\u3000]+(牡|牝|セン)[ \t\u3000]*\d{1,2}歳', title_text)
            if sex_match:
                sex = sex_match.group(1)
            else:
                raise ValueError(f"性別がタイトルから抽出できません: {title_text} ({detail_url})")
            detail_data['sex'] = sex
            if not sex:
                print(f"[異常] 性別が抽出できません: {detail_url}")

            # 血統（父・母・母父）
            sire = ""
            dam = ""
            dam_sire = ""
            pedigree_match = re.search(r'父：([^\u3000]+)\u3000母：([^\u3000]+)\u3000母の父：([^\n]+)', page_text)
            if pedigree_match:
                sire = str(pedigree_match.group(1) or "")
                dam = str(pedigree_match.group(2) or "")
                dam_sire = str(pedigree_match.group(3) or "")
            detail_data['sire'] = str(sire)
            detail_data['dam'] = str(dam)
            detail_data['dam_sire'] = str(dam_sire)
            if not sire:
                print(f"[異常] 父が抽出できません: {detail_url}")
            if not dam:
                print(f"[異常] 母が抽出できません: {detail_url}")
            if not dam_sire:
                print(f"[異常] 母父が抽出できません: {detail_url}")

            # 販売申込者（「（」以降を除去）
            seller = ''
            seller_match = re.search(r'販売申込者：([^\n\r\t]+)', page_text)
            if seller_match:
                seller = seller_match.group(1).strip()
                seller = re.sub(r'（.*$', '', seller).strip()
            detail_data['seller'] = seller
            if not seller:
                print(f"[異常] 販売申込者が抽出できません: {detail_url}")

            # 総賞金（auctionTableRow__priceからlabel=総賞金のvalueを取得）
            total_prize = self._extract_prize_money_from_soup(soup)
            # 総賞金は詳細ページでは設定しない（リストで取得した値を使用）
            # 詳細ページの総賞金は信頼性が低いため、scrape_all_horsesで上書きする
            detail_data['total_prize_start'] = None
            detail_data['total_prize_latest'] = None

            # 賞金情報を正規表現で抽出
            central_prize = 0.0
            local_prize = 0.0
            
            # 中央獲得賞金を抽出
            central_match = re.search(r'中央獲得賞金：([0-9]+(?:\.[0-9]+)?)万円', page_text)
            if central_match:
                central_prize = float(central_match.group(1))
            
            # 地方獲得賞金を抽出
            local_match = re.search(r'地方獲得賞金：([0-9]+(?:\.[0-9]+)?)万円', page_text)
            if local_match:
                local_prize = float(local_match.group(1))
            
            # 総賞金を計算（万円単位で保存）
            total_prize_float = central_prize + local_prize
            detail_data['total_prize_start'] = total_prize_float  # 万円単位で保存
            detail_data['total_prize_latest'] = total_prize_float  # 万円単位で保存
            detail_data['prize'] = f"{total_prize_float}万円"

            # --- ここから主取り判定・入札数取得 ---
            # 開始価格
            start_price = None
            start_price_elem = soup.find('div', class_='itemDetail__price')
            if start_price_elem:
                price_text = start_price_elem.get_text(strip=True)
                match = re.search(r'(\d{1,3}(?:,\d{3})*)', price_text)
                if match:
                    start_price = int(match.group(1).replace(',', ''))
            # 落札価格
            sold_price = None
            # 正規表現で落札価格を抽出（「現在価格」の後の数字を取得）
            sold_price_match = re.search(r'現在価格(\d{1,3}(?:,\d{3})*)円', page_text)
            if sold_price_match:
                sold_price = int(sold_price_match.group(1).replace(',', ''))
            else:
                # fallback: 既存のDOMベース抽出
                sold_price_elem = soup.find('div', class_='itemDetail__soldPrice')
                if sold_price_elem:
                    sold_text = sold_price_elem.get_text(strip=True)
                    match = re.search(r'(\d{1,3}(?:,\d{3})*)', sold_text)
                    if match:
                        sold_price = int(match.group(1).replace(',', ''))
            # 入札数
            bid_num = None
            bid_num_elem = soup.find('b', class_='topBidder__number')
            if bid_num_elem:
                try:
                    bid_num = int(bid_num_elem.get_text(strip=True))
                except Exception:
                    bid_num = None
            # 主取り判定
            unsold = False
            if (bid_num == 0) or (start_price is not None and sold_price is not None and start_price == sold_price):
                unsold = True
            detail_data['start_price'] = start_price
            detail_data['sold_price'] = sold_price
            detail_data['bid_num'] = bid_num
            detail_data['unsold'] = unsold
            # --- ここまで主取り判定・入札数取得 ---

            # コメント（<b>本馬について</b>直下の<pre>を優先）
            comment = self._extract_comment_from_soup(soup)
            if not comment:
                # fallback: 既存ロジック
                desc_div = soup.find('div', class_='itemDetail__description')
                if desc_div and getattr(desc_div, 'text', None):
                    comment = str(desc_div.text).strip() if desc_div.text is not None else ''
                if not comment:
                    remarks_div = soup.find('div', class_='itemDetail__remarks')
                    if remarks_div and getattr(remarks_div, 'text', None):
                        comment = str(remarks_div.text).strip() if remarks_div.text is not None else ''
                if not comment:
                    div = soup.find('div', class_='comment')
                    if div and getattr(div, 'text', None):
                        comment = str(div.text).strip() if div.text is not None else ''
                    else:
                        p = soup.find('p', class_='comment')
                        if p and getattr(p, 'text', None):
                            comment = str(p.text).strip() if p.text is not None else ''
            if not comment:
                print(f"[異常] コメントが抽出できません: {detail_url}")
            detail_data['comment'] = comment

            # その他（既存ロジック）
            detail_data['weight'] = self._extract_weight(soup)
            detail_data['race_record'] = self._extract_race_record(soup)
            detail_data['disease_tags'] = self._extract_disease_tags(detail_data.get('comment', ''))
            detail_data['primary_image'] = self._extract_primary_image(soup)
            detail_data['netkeiba_url'] = self._extract_netkeiba_url(soup)
            return detail_data
        except Exception as e:
            print(f"詳細情報の取得に失敗: {e}")
            return None
    
    def _extract_pedigree_from_page(self, soup) -> dict:
        text = ""
        pre = soup.find('pre')
        if pre and getattr(pre, 'text', None):
            text = str(pre.text).strip() if pre.text is not None else ""
        else:
            for tag in soup.find_all(['div', 'td']):
                tag_text = getattr(tag, 'text', None)
                if tag and tag_text and '父：' in str(tag_text):
                    text = str(tag_text).strip() if tag_text is not None else ""
                    break
        # textは必ずstr型
        text = str(text)
        sire = ""
        dam = ""
        dam_sire = ""
        if '父：' in text and '母：' in text:
            sire = text.split('父：')[1].split('母：')[0].strip()
            if sire is None:
                sire = ''
            else:
                sire = sire.strip() or ''
        if '母：' in text:
            dam = text.split('母：')[1].split('母の父：')[0].strip()
            if dam is None:
                dam = ''
            else:
                dam = dam.strip() or ''
        if '母の父：' in text:
            dam_sire_raw = text.split('母の父：')[1].strip()
            if dam_sire_raw is None:
                dam_sire = ''
            else:
                dam_sire = dam_sire_raw.strip() or ''
        return {
            "sire": sire,
            "dam": dam,
            "dam_sire": dam_sire
        }

    def _extract_weight(self, soup) -> Optional[int]:
        """馬体重を抽出"""
        try:
            page_text = soup.get_text()
            weight_match = re.search(r'(\d{3,4})[㎏kg]', page_text)
            if weight_match:
                return int(weight_match.group(1))
        except Exception as e:
            print(f"馬体重の抽出に失敗: {e}")
        return None
    
    def _extract_race_record(self, soup) -> str:
        """成績を抽出"""
        try:
            page_text = soup.get_text()
            # 成績パターンを探す（例: "24戦4勝［4-6-2-12］"）
            record_match = re.search(r'(\d+戦\d+勝［\d+-\d+-\d+-\d+］)', page_text)
            if record_match:
                result = record_match.group(1)
                if result is not None:
                    return str(result)
        except Exception as e:
            print(f"成績の抽出に失敗: {e}")
        return ""
    
    def _extract_comment(self, soup) -> str:
        """
        コメント欄を素直に抽出する（例：divやpタグ内のテキストを優先的に取得）。
        """
        # 例：div.comment, p.comment, それ以外は最初のdiv/pテキスト
        comment = ""
        div = soup.find('div', class_='comment')
        if div and div.text:
            comment = div.text.strip()
        else:
            p = soup.find('p', class_='comment')
            if p and p.text:
                comment = p.text.strip()
            else:
                # fallback: 最初のdiv/p
                divs = soup.find_all('div')
                for d in divs:
                    if d and d.text and len(d.text.strip()) > 10:
                        comment = d.text.strip()
                        break
                if not comment:
                    ps = soup.find_all('p')
                    for p in ps:
                        if p and p.text and len(p.text.strip()) > 10:
                            comment = p.text.strip()
                            break
        return comment
    
    def _extract_disease_tags(self, comment: str) -> str:
        """疾病タグを抽出"""
        try:
            disease_keywords = ['さく癖', '球節炎', '骨折', '屈腱炎', '蹄葉炎']
            for keyword in disease_keywords:
                if keyword in comment:
                    return keyword
        except Exception as e:
            print(f"疾病タグの抽出に失敗: {e}")
        return "なし"
    
    def _extract_primary_image(self, soup) -> str:
        """馬体画像を抽出"""
        try:
            images = soup.find_all('img', src=True)
            for img in images:
                src = img.get('src', '')
                if 'horse' in src.lower() and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    return src
        except Exception as e:
            print(f"画像の抽出に失敗: {e}")
        return ""
    
    def _extract_netkeiba_url(self, soup) -> str:
        """netkeiba URLを抽出（基本情報を優先）"""
        try:
            links = soup.find_all('a', href=True)
            
            # JBISリンクを探す
            for link in links:
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href:
                    # /record/が付いている場合は除去して基本情報ページのURLを作成
                    if '/record/' in href:
                        basic_info_url = href.replace('/record/', '')
                        # 末尾のスラッシュを追加
                        if not basic_info_url.endswith('/'):
                            basic_info_url += '/'
                        return basic_info_url
                    else:
                        return href
        except Exception as e:
            print(f"netkeiba URLの抽出に失敗: {e}")
        return ""
    
    def _extract_prize_money_from_soup(self, soup: BeautifulSoup) -> Optional[float]:
        """
        <div class="auctionTableRow__price"><div class="label">総獲得賞金</div><div class="value">0.0万円</div></div>
        から総獲得賞金をfloatで抽出。取得できなければNone。
        """
        for price_div in soup.find_all("div", class_="auctionTableRow__price"):
            label = price_div.find("div", class_="label")
            value = price_div.find("div", class_="value")
            if label and value and "総獲得賞金" in label.get_text():
                try:
                    val = value.get_text(strip=True).replace('万円', '').replace(',', '')
                    return float(val)
                except Exception:
                    return None
        return None

    def _extract_comment_from_soup(self, soup: BeautifulSoup) -> str:
        """
        <b>本馬について</b>直下の<pre>内テキストを抽出する。
        """
        for b in soup.find_all("b"):
            if b.get_text(strip=True) == "本馬について":
                pre = b.find_next("pre")
                if pre:
                    return pre.get_text(strip=True) or ""
        return ""
    
    def scrape_all_horses(self, auction_date: Optional[str] = None) -> List[Dict]:
        """全馬のデータを取得"""
        print("=== 楽天オークション スクレイピング開始 ===")
        
        if auction_date is None:
            auction_date = self.get_auction_date()
        
        # 馬のリストを取得
        horses = self.scrape_horse_list()
        
        if not horses:
            print("取得した馬データがありません。")
            return []
        
        print(f"{len(horses)}頭の馬の詳細情報を取得中...")
        
        # 各馬の詳細情報を取得
        for i, horse in enumerate(horses, 1):
            print(f"  {i}/{len(horses)}: {horse['name']}")
            if horse.get('detail_url'):
                detail_data = self.scrape_horse_detail(horse['detail_url'])
                if detail_data:
                    horse.update(detail_data)
                    # sexは必ず詳細ページの値で上書き
                    horse['sex'] = detail_data['sex']
            # サーバーに負荷をかけないよう少し待機
            time.sleep(1)
        
        # JBISから現在の総賞金を取得し、差額を計算
        print("=== JBISから現在の総賞金を取得中... ===")
        for i, horse in enumerate(horses, 1):
            print(f"  {i}/{len(horses)}: {horse['name']} - JBIS賞金取得中...")
            
            # JBISから現在の総賞金を取得
            if horse.get('jbis_url'):
                try:
                    # JBISの基本情報ページから総賞金を取得
                    jbis_response = self.session.get(horse['jbis_url'], timeout=30)
                    jbis_response.raise_for_status()
                    jbis_soup = BeautifulSoup(jbis_response.content, 'html.parser')
                    
                    # 総賞金を抽出（JBISのページ構造に合わせて修正）
                    total_prize_latest = None
                    page_text = jbis_soup.get_text()
                    
                    # 「総賞金X.X万円」のパターンを探す
                    prize_match = re.search(r'総賞金([\d,]+\.?\d*)万円', page_text)
                    if prize_match:
                        prize_str = prize_match.group(1).replace(',', '')
                        total_prize_latest = float(prize_str)
                    else:
                        # フォールバック: 他の賞金パターンを探す
                        prize_match = re.search(r'([\d,]+\.?\d*)万円', page_text)
                        if prize_match:
                            prize_str = prize_match.group(1).replace(',', '')
                            total_prize_latest = float(prize_str)
                    
                    if total_prize_latest is not None:
                        # オークション時と現在の賞金を比較して、より信頼性の高い方を採用
                        start_prize = horse.get('total_prize_start', 0)
                        
                        # オークション直後の場合は、オークション時の賞金を優先
                        # 数ヶ月後は現在の賞金を採用
                        if start_prize > 0 and total_prize_latest == 0:
                            # オークション時は賞金があるが、現在は0 → オークション時の値を採用
                            horse['total_prize_latest'] = start_prize
                        elif start_prize == 0 and total_prize_latest > 0:
                            # オークション時は0だが、現在は賞金がある → 現在の値を採用
                            horse['total_prize_start'] = total_prize_latest
                            horse['total_prize_latest'] = total_prize_latest
                        else:
                            # 通常の差額計算
                            horse['total_prize_latest'] = total_prize_latest
                            diff = round(total_prize_latest - start_prize, 1)
                            sign = '+' if diff >= 0 else ''
                            horse['prize_diff'] = f"{sign}{diff}万円"
                    else:
                        horse['prize_diff'] = '-'
                        
                except Exception as e:
                    print(f"    JBIS賞金取得に失敗: {e}")
                    horse['prize_diff'] = '-'
            else:
                horse['prize_diff'] = '-'
            
            # サーバーに負荷をかけないよう少し待機
            time.sleep(1)
        
        # 共通フィールドを追加
        for i, horse in enumerate(horses, 1):
            horse['id'] = i  # IDを追加
            horse['auction_date'] = auction_date
            horse['created_at'] = datetime.now().isoformat()
            horse['updated_at'] = datetime.now().isoformat()
        
        print(f"=== スクレイピング完了: {len(horses)}頭の馬データを取得 ===")
        return horses

    def get_jbis_basic_info_url_from_detail(self, detail_url: str) -> str:
        """
        楽天オークション詳細ページからJBIS基本情報ページのURLを取得する（recordを除去して返す）
        """
        try:
            print(f"楽天詳細ページからJBIS基本情報URL取得: {detail_url}")
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href and '/record/' in href:
                    # /record/を除去し、末尾にスラッシュを付与
                    basic_info_url = href.replace('/record/', '')
                    if not basic_info_url.endswith('/'):
                        basic_info_url += '/'
                    print(f"DEBUG: JBIS基本情報URL: {basic_info_url}")
                    return basic_info_url
            print("JBISリンクが見つかりませんでした")
            return ''
        except Exception as e:
            print(f"JBIS基本情報URLの取得に失敗: {e}")
            return ''

# === テスト関数 ===
def test_extract_pedigree():
    class DummySoup:
        def __init__(self, text):
            self._text = text
        def get_text(self, separator=' ', strip=True):
            return self._text
        def find(self, tag, class_=None):
            class Dummy:
                def __init__(self, text):
                    self.text = text
            if tag == 'pre':
                return Dummy(self._text)
            return None
        def find_all(self, tags):
            class Dummy:
                def __init__(self, text):
                    self.text = text
            return [Dummy(self._text)]
    # テストパターン
    patterns = [
        "父：イスラボニータ　母：ハイエストクイーン　母の父：シンボリクリスエス",
        "父：ディープインパクト 母：ウインドインハーヘア 母の父：Alzao",
        "父：キングカメハメハ　母：マンファス　母の父：Last Tycoon",
        "父：ハーツクライ(成績:GI馬) 母：アイリッシュダンス(重賞馬) 母の父：トニービン",
        "父：オルフェーヴル　母：オリエンタルアート　母の父：メジロマックイーン",
        "父：ロードカナロア　母：レディブラッサム　母の父：Storm Cat",
        "父：エピファネイア　母：シーザリオ　母の父：スペシャルウィーク",
        "父：キズナ　母：キャットクイル　母の父：Storm Cat",
        "父：サンデーサイレンス　母：ウインドインハーヘア",
        "父：ダイワメジャー　母：スカーレットブーケ",
        "父：キングカメハメハ",
        "母：ウインドインハーヘア",
        "母の父：Alzao",
        "父：ディープインパクト(成績:7冠馬) 母：ウインドインハーヘア(重賞馬) 母の父：Alzao(海外馬)",
    ]
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
    scraper = RakutenAuctionScraper()
    for i, text in enumerate(patterns):
        soup = DummySoup(text)
        result = scraper._extract_pedigree_from_page(soup)
        print(f"--- パターン{i+1} ---\n入力: {text}\n抽出結果: {result}\n")
# テスト実行
if __name__ == "__main__":
    # test_extract_pedigree() をコメントアウトし、実スクレイピングを実行
    # test_extract_pedigree()
    scraper = RakutenAuctionScraper()
    horses = scraper.scrape_all_horses()
    # 取得した馬データの件数とサンプルを表示
    print(f"取得馬数: {len(horses)}")
    if horses:
        print("サンプル馬データ:")
        print(horses[0]) 