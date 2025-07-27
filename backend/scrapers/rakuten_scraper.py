import re
import time
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union, cast
from datetime import datetime

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
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
        
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
            print(f"User-Agent: {self.session.headers.get('User-Agent', 'N/A')}")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            print(f"レスポンスステータス: {response.status_code}")
            print(f"レスポンスサイズ: {len(response.content)} bytes")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # デバッグ: ページタイトルを確認
            title = soup.find('title')
            if title:
                print(f"ページタイトル: {title.get_text(strip=True)}")
            
            # デバッグ: 全div要素の数を確認
            all_divs = soup.find_all('div')
            print(f"全div要素数: {len(all_divs)}")
            
            # auctionTableCardクラスのdivを全て取得
            cards = soup.find_all('div', class_='auctionTableCard')
            print(f"auctionTableCard要素数: {len(cards)}")
            
            # デバッグ: 他のauction関連クラスも確認
            auction_elements = soup.find_all(class_=lambda x: x and 'auction' in x)
            print(f"auctionを含むクラス要素数: {len(auction_elements)}")
            
            if len(auction_elements) > 0:
                print("auction関連クラスの例:")
                for i, elem in enumerate(auction_elements[:5]):
                    print(f"  {i+1}. {elem.get('class', [])}")
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
            # total_prize = self._extract_prize_money_from_soup(soup)  # ←未実装なので削除
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
            comment = ''
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
            detail_data['jbis_url'] = self._extract_jbis_url(soup)

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
        
        try:
            # 正規表現で精密に抽出
            import re
            
            # 父、母、母の父を一度に抽出
            pedigree_pattern = r'父：([^\u3000\n\r]+?)\s*母：([^\u3000\n\r]+?)\s*母の父：([^\n\r\u3000]+?)(?=\s|\n|\r|$)'
            pedigree_match = re.search(pedigree_pattern, text)
            
            if pedigree_match:
                sire = pedigree_match.group(1).strip()
                dam = pedigree_match.group(2).strip()
                dam_sire = pedigree_match.group(3).strip()
            else:
                # フォールバック: 従来のロジックを改善
                if '父：' in text and '母：' in text:
                    sire_part = text.split('父：')[1].split('母：')[0]
                    sire = re.sub(r'[\n\r\u3000]+', ' ', sire_part).strip()
                
                if '母：' in text and '母の父：' in text:
                    dam_part = text.split('母：')[1].split('母の父：')[0]
                    dam = re.sub(r'[\n\r\u3000]+', ' ', dam_part).strip()
                
                if '母の父：' in text:
                    dam_sire_part = text.split('母の父：')[1]
                    # 最初の単語または行までを抽出
                    dam_sire_match = re.match(r'([^\n\r\u3000]+)', dam_sire_part)
                    if dam_sire_match:
                        dam_sire = dam_sire_match.group(1).strip()
                    else:
                        dam_sire = dam_sire_part.split('\n')[0].split('\r')[0].strip()
            
            # 空白やNoneのチェック
            sire = sire.strip() if sire else ""
            dam = dam.strip() if dam else ""
            dam_sire = dam_sire.strip() if dam_sire else ""
            
        except Exception as e:
            print(f"血統情報の抽出に失敗: {e}")
            sire = ""
            dam = ""
            dam_sire = ""
        
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
        コメント欄を抽出する（「本馬について」セクションの<hr>以降のテキスト）。
        """
        comment = ""
        
        try:
            # 「本馬について」のテキストを含む要素を検索
            about_horse_elements = soup.find_all(text=lambda text: text and '本馬について' in text)
            
            if about_horse_elements:
                # 「本馬について」を含む要素の親要素から開始
                for about_text in about_horse_elements:
                    parent = about_text.parent
                    if not parent:
                        continue
                    
                    # 親要素から<hr>タグを探す
                    hr_tag = None
                    
                    # 同じ親要素内で<hr>を探す
                    hr_tag = parent.find('hr')
                    
                    # 見つからない場合は、親要素の次の兄弟要素で<hr>を探す
                    if not hr_tag:
                        current = parent
                        while current:
                            next_sibling = current.find_next_sibling()
                            if next_sibling:
                                if next_sibling.name == 'hr':
                                    hr_tag = next_sibling
                                    break
                                hr_tag = next_sibling.find('hr')
                                if hr_tag:
                                    break
                            current = next_sibling
                    
                    # <hr>以降のテキストを抽出
                    if hr_tag:
                        comment_parts = []
                        current = hr_tag.next_sibling
                        
                        while current:
                            if hasattr(current, 'get_text'):
                                text = current.get_text().strip()
                                if text and len(text) > 0:
                                    comment_parts.append(text)
                            elif isinstance(current, str):
                                text = current.strip()
                                if text and len(text) > 0:
                                    comment_parts.append(text)
                            current = current.next_sibling
                        
                        if comment_parts:
                            comment = ' '.join(comment_parts).strip()
                            break
            
            # フォールバック: 従来のロジック
            if not comment:
                div = soup.find('div', class_='comment')
                if div and div.text:
                    comment = div.text.strip()
                else:
                    p = soup.find('p', class_='comment')
                    if p and p.text:
                        comment = p.text.strip()
            
            # コメントの整形
            if comment:
                # 改行を適切に処理
                comment = ' '.join(comment.split())
                    
        except Exception as e:
            print(f"コメントの抽出に失敗: {e}")
            comment = ""
        
        return comment
    
    def _extract_disease_tags(self, comment: str) -> str:
        """
        コメントから疾病タグを抽出（複数該当時はカンマ区切り、重複なし）
        
        Args:
            comment: 抽出対象のコメントテキスト
            
        Returns:
            str: 抽出されたタグをカンマ区切りで返す。該当なしの場合は空文字を返す
        """
        try:
            if not comment or not isinstance(comment, str):
                print("【デバッグ】コメントが空または文字列ではありません")
                return ""
                
            print(f"【デバッグ】コメントの最初の100文字: {comment[:100]}...")  # デバッグ用
            
            # 正規化: 全角・半角の統一、改行・タブをスペースに置換
            normalized_comment = comment.translate(
                str.maketrans({
                    '\n': ' ', '\t': ' ', '　': ' ',  # 全角スペースも半角に
                    '（': '(', '）': ')', '［': '[', '］': ']',
                    '，': ',', '．': '.', '：': ':', '；': ';',
                    '・': ' ', '、': ' ', '。': ' '  # 句読点もスペースに
                })
            )
            
            print(f"【デバッグ】正規化後: {normalized_comment[:100]}...")  # デバッグ用
            
            # 疾病キーワードと正規表現パターンのマッピング（シンプル化）
            disease_patterns = {
                '骨折': [r'骨折', r'こっせつ'],
                '屈腱炎': [r'屈腱炎', r'くっけんえん'],
                '球節炎': [r'球節炎', r'きゅうせつえん'],
                '蹄葉炎': [r'蹄葉炎', r'ていようえん'],
                '靭帯損傷': [r'靭帯(損傷|断裂)'],
                '捻挫': [r'捻挫', r'ねんざ'],
                '腫れ': [r'腫[れ脹]', r'はれ'],
                '炎症': [r'(?<![無な])炎症', r'えんしょう(?![なな])'],
                '裂蹄': [r'裂蹄', r'れってい'],
                '骨瘤': [r'骨瘤', r'こつりゅう'],
                '関節炎': [r'関節炎', r'かんせつえん'],
                '筋炎': [r'筋炎', r'きんえん'],
                '筋肉痛': [r'筋肉痛', r'きんにくつう'],
                '神経麻痺': [r'神経麻痺', r'しんけいまひ'],
                '腰痛': [r'腰痛', r'ようつう'],
                '跛行': [r'跛行', r'はこう'],
                '蹄壁疾患': [r'蹄壁(疾患|異常)'],
                '蹄叉腐爛': [r'蹄叉腐爛', r'ていさふらん'],
                '骨膜炎': [r'骨膜炎', r'こつまくえん'],
                '亀裂': [r'亀裂', r'きれつ'],
                '外傷': [r'外傷', r'がいしょう'],
                '脱臼': [r'脱[臼]?', r'だっ[きゅう]'],
                '肉離れ': [r'肉離れ', r'にくばなれ'],
                '裂傷': [r'裂傷', r'れっしょう'],
                '打撲': [r'打撲', r'だぼく'],
                '挫傷': [r'挫傷', r'ざしょう'],
                '腫瘍': [r'腫瘍', r'しゅよう'],
                '出血': [r'出血', r'しゅっけつ'],
                '貧血': [r'貧血', r'ひんけつ'],
                '皮膚病': [r'皮膚病', r'ひふびょう', r'皮膚炎'],
                '呼吸器疾患': [r'呼吸器(疾患|異常)'],
                '心臓病': [r'心臓(病|疾患|異常)'],
                '腎臓病': [r'腎臓(病|疾患|異常)'],
                '肝臓病': [r'肝臓(病|疾患|異常)'],
                '消化器疾患': [r'消化器(疾患|異常)'],
                '眼病': [r'眼(病|疾患|異常)'],
                '歯牙疾患': [r'歯(牙)?(疾患|異常)'],
                '蹄病': [r'蹄(病|疾患|異常)'],
                '関節疾患': [r'関節(疾患|異常)'],
                '骨疾患': [r'骨(疾患|異常)'],
                '筋肉疾患': [r'筋肉(疾患|異常)'],
                '神経疾患': [r'神経(疾患|異常)'],
                '循環器疾患': [r'循環器(疾患|異常)'],
                '感染症': [r'感染症', r'かんせんしょう'],
                'ウイルス性疾患': [r'ウイルス(性)?(疾患|感染)'],
                '細菌性疾患': [r'細菌(性)?(疾患|感染)'],
                '真菌性疾患': [r'真菌(性)?(疾患|感染)'],
                'アレルギー': [r'アレルギー', r'あれるぎー'],
                '自己免疫疾患': [r'自己免疫(疾患|異常)'],
                '代謝性疾患': [r'代謝(性)?(疾患|異常)'],
                '内分泌疾患': [r'内分泌(疾患|異常)'],
                '腫瘍性疾患': [r'腫瘍(性)?(疾患|異常)'],
                '先天性疾患': [r'先天性(疾患|異常)'],
                '後天性疾患': [r'後天性(疾患|異常)'],
                '外傷性疾患': [r'外傷(性)?(疾患|異常)'],
                '中毒性疾患': [r'中毒(性)?(疾患|異常)'],
                '栄養性疾患': [r'栄養(性)?(疾患|異常)'],
                '環境性疾患': [r'環境(性)?(疾患|異常)'],
                'ストレス性疾患': [r'ストレス(性)?(疾患|異常)'],
                '加齢性疾患': [r'加齢(性)?(疾患|異常)']
            }
            
            # 除外パターン（整理版）
            exclude_patterns = [
                # 骨折関連の除外パターン
                r'骨折[な無]い',         # 「骨折ない」
                r'骨折[はも]?無い',      # 「骨折は無い」「骨折も無い」
                r'骨折[はも]?ない',      # 「骨折はない」「骨折もない」
                r'骨折[はも]?無し',      # 「骨折は無し」「骨折も無し」
                r'骨折[はも]?なし',      # 「骨折はなし」「骨折もなし」
                r'骨折[はも]?無',        # 「骨折は無」「骨折も無」
                r'骨折[はも]?無[かっ]?た', # 「骨折は無かった」「骨折も無かった」
                r'骨折[はも]?な[かっ]?た', # 「骨折はなかった」「骨折もなかった」
                r'骨折[はも]?無いです',  # 「骨折は無いです」「骨折も無いです」
                r'骨折[はも]?無いと',    # 「骨折は無いと」「骨折も無いと」
                r'骨折[はも]?無いが',    # 「骨折は無いが」「骨折も無いが」
                r'骨折[はも]?無いので',  # 「骨折は無いので」「骨折も無いので」
                r'無骨折',               # 「無骨折」
                
                # 炎症関連の除外パターン
                r'[な無]?炎症',          # 「無炎症」「な炎症」
                r'炎症[はも]?無い',      # 「炎症は無い」「炎症も無い」
                r'炎症[はも]?ない',      # 「炎症はない」「炎症もない」
                r'炎症[はも]?無し',      # 「炎症は無し」「炎症も無し」
                r'炎症[はも]?なし',      # 「炎症はなし」「炎症もなし」
                r'炎症[はも]?無',        # 「炎症は無」「炎症も無」
                r'炎症[はも]?無かった',  # 「炎症は無かった」「炎症も無かった」
                r'炎症[はも]?な[かっ]?た', # 「炎症はなかった」「炎症もなかった」
                r'炎症[はも]?無[かっ]?た', # 「炎症は無かった」「炎症も無かった」
                r'炎症[はも]?無いです',  # 「炎症は無いです」「炎症も無いです」
                r'炎症[はも]?無いと',    # 「炎症は無いと」「炎症も無いと」
                r'炎症[はも]?無いが',    # 「炎症は無いが」「炎症も無いが」
                r'炎症[はも]?無いので',  # 「炎症は無いので」「炎症も無いので」
                
                # その他の一般的な除外パターン
                r'異常[な無]',    # 「異常なし」「異常な」
                r'問題[な無]',    # 「問題なし」「問題な」
                r'心配[な無]',    # 「心配なし」「心配な」
                r'懸念[な無]',    # 「懸念なし」「懸念な」
                r'所見[な無]',    # 「所見なし」「所見な」
                r'特記[な無]',    # 「特記なし」「特記な」
                r'以上[な無]',    # 「以上なし」「以上な」
                r'その他[な無]',  # 「その他なし」「その他な」
                r'特にな[し無]',  # 「特になし」「特に無」
                r'現在[はも]?無い', # 「現在は無い」「現在も無い」
                r'現在[はも]?ない', # 「現在はない」「現在もない」
                r'現在[はも]?無し', # 「現在は無し」「現在も無し」
                r'現在[はも]?なし', # 「現在はなし」「現在もなし」
                r'現在[はも]?無',   # 「現在は無」「現在も無」
                r'現在[はも]?無かった', # 「現在は無かった」「現在も無かった」
                r'現在[はも]?な[かっ]?た', # 「現在はなかった」「現在もなかった」
                r'現在[はも]?無[かっ]?た', # 「現在は無かった」「現在も無かった」
                r'現在[はも]?無いです', # 「現在は無いです」「現在も無いです」
                r'現在[はも]?無いと',   # 「現在は無いと」「現在も無いと」
                r'現在[はも]?無いが',   # 「現在は無いが」「現在も無いが」
                r'現在[はも]?無いので'  # 「現在は無いので」「現在も無いので」
            ]
            
            found = set()
            
            # 各パターンでマッチング
            for tag, patterns in disease_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, normalized_comment, re.IGNORECASE):
                        found.add(tag)
                        break  # 1つでもマッチしたら次のタグへ
            
            # 除外パターンにマッチするタグを削除
            filtered_tags = []
            for tag in found:
                exclude = False
                for pattern in exclude_patterns:
                    if re.search(pattern, normalized_comment, re.IGNORECASE):
                        exclude = True
                        break
                if not exclude:
                    filtered_tags.append(tag)
            
            # 重複を削除してソート
            unique_sorted_tags = sorted(list(set(filtered_tags)))
            
            # デバッグ用に抽出されたタグをログに出力
            if unique_sorted_tags:
                print(f"抽出された疾病タグ: {', '.join(unique_sorted_tags)}")
            
            return ','.join(unique_sorted_tags) if unique_sorted_tags else ""
            
        except Exception as e:
            print(f"疾病タグの抽出に失敗: {e}")
            return ""
    
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

    def _extract_jbis_url(self, soup) -> str:
        """JBIS URLを抽出（基本情報を優先）"""
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
            print(f"JBIS URLの抽出に失敗: {e}")
        return ""

    def _normalize_jbis_url(self, jbis_url: str) -> str:
        """JBIS URLを基本情報ページのURLに正規化する"""
        if not jbis_url:
            return jbis_url
        
        # /pedigree/ や /record/ を除去して基本情報ページのURLに変換
        normalized_url = jbis_url
        if '/pedigree/' in jbis_url:
            normalized_url = jbis_url.replace('/pedigree/', '/')
        elif '/record/' in jbis_url:
            normalized_url = jbis_url.replace('/record/', '/')
        
        # 末尾のスラッシュを確保
        if not normalized_url.endswith('/'):
            normalized_url += '/'
        
        return normalized_url

    def _extract_seller(self, page_text: str) -> str:
        """販売申込者を抽出"""
        seller_match = re.search(r'販売申込者：([^\n\r\t]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            seller = re.sub(r'（.*$', '', seller).strip()
            return seller
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
                    # JBIS URLを正規化（血統情報ページを基本情報ページに変換）
                    normalized_jbis_url = self._normalize_jbis_url(horse['jbis_url'])
                    if normalized_jbis_url != horse['jbis_url']:
                        print(f"    JBIS URL正規化: {horse['jbis_url']} -> {normalized_jbis_url}")
                    
                    # JBISの基本情報ページから総賞金を取得
                    jbis_response = self.session.get(normalized_jbis_url, timeout=30)
                    jbis_response.raise_for_status()
                    jbis_soup = BeautifulSoup(jbis_response.content, 'html.parser')
                    
                    # 総賞金を抽出（JBISのページ構造に合わせて修正）
                    total_prize_latest = None
                    
                    # 方法1: dtタグから総賞金を取得（最も確実）
                    total_prize_dt = jbis_soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                    if total_prize_dt:
                        dd = total_prize_dt.find_next_sibling('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            # 数値を抽出（例: "9077.9万円" -> 9077.9）
                            prize_num_match = re.search(r'([\d,]+\.?\d*)', prize_text)
                            if prize_num_match:
                                try:
                                    prize_str = prize_num_match.group(1).replace(',', '')
                                    total_prize_latest = float(prize_str)
                                    print(f"    dtタグから賞金取得成功: {total_prize_latest}万円")
                                except ValueError:
                                    print(f"    dtタグの賞金を数値変換できませんでした: {prize_text}")
                    
                    # 方法2: スペースを考慮した正規表現（dtタグが失敗した場合のフォールバック）
                    if total_prize_latest is None:
                        page_text = jbis_soup.get_text()
                        # スペースを考慮したパターン
                        prize_match = re.search(r'総賞金\s*([\d,]+\.?\d*)\s*万円', page_text)
                        if prize_match:
                            try:
                                prize_str = prize_match.group(1).replace(',', '')
                                total_prize_latest = float(prize_str)
                                print(f"    正規表現から賞金取得成功: {total_prize_latest}万円")
                            except ValueError:
                                print(f"    正規表現の賞金を数値変換できませんでした: {prize_match.group(1)}")
                        else:
                            print(f"    賞金データが見つかりませんでした")
                    
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