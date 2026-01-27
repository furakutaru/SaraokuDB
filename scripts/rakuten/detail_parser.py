"""楽天競馬オークション詳細ページの共通パーサー"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup
from urllib.parse import urljoin

from scripts.components.comment_extractor import CommentExtractor
from scripts.components.horse_info_extractor import HorseInfoExtractor
from scripts.components.price_extractor import PriceExtractor
from scripts.components.price_info_extractor import PriceInfoExtractor
from scripts.components.race_record_extractor import RaceRecordExtractor
from scripts.components.seller_info_extractor import SellerInfoExtractor


logger = logging.getLogger(__name__)
BROODMARE_KEYWORDS = ("繁殖牝馬", "※繁殖牝馬", "受胎")


@dataclass
class DetailParseResult:
    name: str
    auction_id: str
    raw_name: Optional[str] = None
    is_broodmare: bool = False
    sex: Optional[str] = None
    age: Optional[int] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    weight: Optional[int] = None
    seller: Optional[str] = None
    sold_price: Optional[int] = None
    is_unsold: bool = False
    bid_count: Optional[int] = None
    comment: Optional[str] = None
    disease_tags: Optional[str] = None
    auction_date: Optional[str] = None
    image_url: Optional[str] = None
    jbis_url: Optional[str] = None
    detail_url: Optional[str] = None
    race_record: Optional[str] = None
    scraped_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    # 最新賞金（円）。詳細ページから推定抽出した合算値を格納
    total_prize_latest: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


_horse_info_extractor = HorseInfoExtractor(logger=logger.getChild("horse_info"))
_seller_extractor = SellerInfoExtractor(logger=logger.getChild("seller"))
_comment_extractor = CommentExtractor(logger=logger.getChild("comment"))
_price_extractor = PriceExtractor()
_price_info_extractor = PriceInfoExtractor(logger=logger.getChild("price_info"))
_race_record_extractor = RaceRecordExtractor(logger=logger.getChild("race_record"))


def _extract_name(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    candidates = [
        ("span", {"itemprop": "name"}),
        ("h1", {"class": re.compile("horseName")}),
        ("title", {}),
    ]
    for tag, attrs in candidates:
        elem = soup.find(tag, attrs=attrs) if attrs else soup.find(tag)
        if elem and elem.get_text(strip=True):
            text = elem.get_text(strip=True).split("|")[0].strip()
            cleaned = _clean_horse_name(text)
            return cleaned, text
    return None, None


def _extract_image_url(soup: BeautifulSoup) -> Optional[str]:
    """
    詳細ページから代表画像のURLを抽出する。可能な限り確度の高い順にフォールバックする。
    - meta og:image
    - クラスに image を含む img
    - 「商品画像」セクション直下の img
    - 任意の img のうち auction ドメインのものを優先
    - data-src / data-original / srcset にも対応
    """

    def normalize_src(raw: Optional[str]) -> Optional[str]:
        if not raw:
            return None
        src = raw.strip()
        if src.startswith('//'):
            return 'https:' + src
        if src.startswith('/'):  # 相対パスは keiba.r10s.jp を既定ドメインとして補完
            return urljoin('https://keiba.r10s.jp', src)
        return src

    def is_probably_logo(u: str) -> bool:
        lname = u.lower()
        return any(x in lname for x in ['logo', 'favicon', 'apple_touch', 'icon']) or '/_nuxt/' in lname

    def has_img_ext(u: str) -> bool:
        return re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', u.lower()) is not None

    # 1) meta og:image / twitter:image / link rel=image_src
    for sel in [
        ('meta', {'property': 'og:image'}, 'content'),
        ('meta', {'name': 'twitter:image'}, 'content'),
        ('link', {'rel': ['image_src', 'thumbnail']}, 'href')
    ]:
        tag = soup.find(sel[0], attrs=sel[1])
        if tag and tag.get(sel[2]):
            cand = normalize_src(tag.get(sel[2]))
            if cand and not is_probably_logo(cand) and has_img_ext(cand):
                return cand

    # 1.5) 生HTMLから /auction/data/item/... の実画像URLを直接抽出（Nuxt等でimgタグが変形していても対応）
    try:
        html_text = str(soup)
        # 例: https://keiba.r10s.jp/auction/data/item/1/251026_horse_03/１.jpeg
        m = re.search(r'(https?:\/\/keiba\.r10s\.jp)?(\/auction\/data\/item\/[^"]+?\.(?:jpe?g|png|webp))', html_text, re.I)
        if m:
            base = m.group(1) or 'https://keiba.r10s.jp'
            path = m.group(2)
            url = urljoin(base, path)
            if url and has_img_ext(url) and not is_probably_logo(url):
                return url
    except Exception:
        pass

    # 2) クラスに image を含む img（horse/item/product を含む場合を優先）
    img = soup.find('img', {"class": re.compile(r"(horse|item|product).*(image)|image", re.I)})
    if img:
        for attr in ['src', 'data-src', 'data-original']:
            val = img.get(attr)
            if val:
                cand = normalize_src(val)
                if cand and not is_probably_logo(cand):
                    return cand
        # srcset 対応（最初のURLを使用）
        srcset = img.get('srcset')
        if srcset:
            cand = normalize_src(srcset.split(',')[0].split()[0])
            if cand and not is_probably_logo(cand):
                return cand

    # 3) 「商品画像」セクション付近の img
    product_heading = soup.find(
        lambda t: t and t.name in ['h1','h2','h3','h4','div','span','p'] and re.search(r'(商品画像|商品写真|画像|写真)', t.get_text(strip=True) or '')
    )
    if product_heading:
        container = product_heading.find_parent()
        if container:
            # セクション内の全imgからスコアリングで選択
            section_imgs = container.find_all('img')
            best = None
            best_score = -999
            for im in section_imgs:
                val = None
                for attr in ['src', 'data-src', 'data-original']:
                    if im.get(attr):
                        val = im.get(attr)
                        break
                if not val and im.get('srcset'):
                    val = im.get('srcset').split(',')[0].split()[0]
                cand = normalize_src(val)
                if not cand:
                    continue
                score = 0
                lname = cand.lower()
                if 'keiba.r10s.jp' in lname or '/auction/' in lname:
                    score += 2
                if has_img_ext(lname):
                    score += 2
                if is_probably_logo(lname):
                    score -= 3
                try:
                    w = int(im.get('width') or 0)
                    h = int(im.get('height') or 0)
                    if w >= 200 or h >= 200:
                        score += 1
                except Exception:
                    pass
                if score > best_score:
                    best = cand
                    best_score = score
            if best and best_score > 0:
                return best

    # 4) 任意の img を走査し、スコアリングして最適候補を選ぶ
    #    ロゴ類や/_nuxt/配下のアセットは低スコアとし、実画像を優先
    candidates: list[tuple[str, int]] = []
    for im in soup.find_all('img'):
        val = None
        for attr in ['src', 'data-src', 'data-original']:
            if im.get(attr):
                val = im.get(attr)
                break
        if not val and im.get('srcset'):
            val = im.get('srcset').split(',')[0].split()[0]
        norm = normalize_src(val)
        if not norm:
            continue

        score = 0
        lname = norm.lower()
        if 'keiba.r10s.jp' in lname or '/auction/' in lname:
            score += 2
        if re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', lname):
            score += 2
        if '/_nuxt/' in lname:
            score -= 3
        if any(x in lname for x in ['logo', 'favicon', 'apple_touch', 'icon']):
            score -= 3
        # サイズ属性があれば大きめを優先
        try:
            w = int(im.get('width') or 0)
            h = int(im.get('height') or 0)
            if w >= 200 or h >= 200:
                score += 1
        except Exception:
            pass
        candidates.append((norm, score))

    # フィルタリング: 明らかなロゴ/アイコンを除外し、画像拡張子を優先
    def is_probably_logo(u: str) -> bool:
        lname = u.lower()
        return any(x in lname for x in ['logo', 'favicon', 'apple_touch', 'icon'])

    def has_img_ext(u: str) -> bool:
        return re.search(r'\.(jpg|jpeg|png|webp)(\?|$)', u.lower()) is not None

    if candidates:
        # スコアの高い順に選択し、スコアが0以下のみの場合は見送り（ロゴ等の可能性が高い）
        candidates.sort(key=lambda x: x[1], reverse=True)
        if candidates[0][1] > 0:
            return candidates[0][0]
        # すべてスコア <= 0 の場合は None を返してロゴ誤検出を回避
        return None

    return None


def _extract_jbis_url(soup: BeautifulSoup) -> Optional[str]:
    anchor = soup.find("a", href=lambda href: href and "jbis.or.jp" in href)
    if anchor and anchor.get("href"):
        return anchor["href"].strip()
    return None


def _extract_bid_count(html: str) -> Optional[int]:
    # 入札数 : 1 や 入札数:1 、あるいは改行を含むケースに対応
    # "入札情報" のような他の単語にマッチしないように注意
    match = re.search(r"入札数\s*[:：]?\s*(\d+)", html)
    if not match:
        # 具体的なHTML構造: <div class="topBidder__textLabel">入札数</div> ... <a ...>1</a>
        # テキストベースで "入札数" の後に来る最初の数字を探す（少し乱暴だがフォールバックとして）
        soup = BeautifulSoup(html, "html.parser")
        # 特定のクラスを探す
        label = soup.find(string=re.compile(r"入札数"))
        if label:
            # 親要素や隣接要素から数字を探す
            parent = label.find_parent()
            if parent:
                parent_container = parent.parent
                if parent_container:
                     bid_num_elem = parent_container.find("a", href=lambda h: h and "bidInfo" in h)
                     if bid_num_elem:
                         try:
                             return int(bid_num_elem.get_text(strip=True))
                         except:
                             pass
    
    if match:
        return int(match.group(1))
    return None


def _extract_prize_info(html: str) -> Dict[str, Optional[int]]:
    """
    詳細ページHTMLから中央/地方/総の賞金情報を抽出し、合算した現在賞金を返す
    戻り値は円単位の整数（見つからない場合は None）
    併せて最終更新らしき日付も推定抽出する
    """
    result: Dict[str, Optional[int]] = {
        "central_prize_money": None,
        "local_prize_money": None,
        "total_prize_money": None,
        "last_prize_update": None,
    }
    try:
        # タグ除去してテキストのみで判定（Vueレンダリング後の静的HTMLでも拾えるように）
        try:
            soup = BeautifulSoup(html, "html.parser")
            text = soup.get_text(" ")
        except Exception:
            text = html
        # 数値抽出（「1,234.5万円」「1,234万円」「123,456円」などに対応）
        def to_yen(value_text: str) -> Optional[int]:
            text = value_text.replace(',', '').strip()
            m_man = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*万\s*円?", text)
            if m_man:
                try:
                    return int(float(m_man.group(1)) * 10000)
                except Exception:
                    return None
            m_yen = re.search(r"([0-9]+)\s*円", text)
            if m_yen:
                try:
                    return int(m_yen.group(1))
                except Exception:
                    return None
            # 純数字だけの場合
            m_num = re.search(r"^[0-9]+(?:\.[0-9]+)?$", text)
            if m_num:
                try:
                    # 単位不明だが円として扱う（安全側）
                    return int(float(m_num.group(0)))
                except Exception:
                    return None
            return None

        # 1. <pre>タグ内のテキストを優先的に取得（詳細情報は pre 内に書かれることが多い）
        pre_text = ""
        pre_tag = soup.find("pre")
        if pre_tag:
            pre_text = pre_tag.get_text(" ")
        
        # 検索対象テキストのリスト（優先度順: pre内 -> body全体）
        target_texts = [pre_text, text]

        # ラベルに基づき中央/地方/総を探す
        # キーワードは柔軟に: 「中央」「JRA」「地方」「NAR」「総」「合計」
        def extract_by_label(patterns: list[str]) -> Optional[int]:
            for tgt_text in target_texts:
                if not tgt_text:
                    continue
                # 全角スペース等を半角に寄せてから検索
                normalized = tgt_text.replace('\u3000', ' ').replace('\xa0', ' ')
                for pat in patterns:
                    # 改行をまたぐ可能性も考慮して re.DOTALL は使わないが、
                    # 前後の文脈を含めて検索
                    m = re.search(pat + r"\s*[:：]?\s*([0-9,.]+\s*(?:万|円)?)", normalized)
                    if m:
                        yen = to_yen(m.group(1))
                        if yen is not None:
                            return yen
            return None
            for pat in patterns:
                m = re.search(pat + r"\s*[:：]?\s*([^\n\r<]+)", text, re.IGNORECASE)
                if m:
                    yen = to_yen(m.group(1))
                    if yen is not None:
                        return yen
            return None

        central = extract_by_label([r"中央.*?賞金", r"JRA.*?賞金", r"中央獲得賞金"]) or None
        local = extract_by_label([r"地方.*?賞金", r"NAR.*?賞金", r"地方獲得賞金"]) or None
        total = extract_by_label([r"総.*?賞金", r"合計.*?賞金", r"総獲得賞金"]) or None

        # 明示的パターンのフォールバック（同一行に『中央獲得賞金：X万円　地方獲得賞金：Y万円』のように並ぶケース）
        if central is None or local is None:
            try:
                # 全角スペース等を半角に寄せてから検索
                normalized = text.replace('\u3000', ' ')
                m_c = re.search(r"中央\s*獲得?賞金\s*[:：]?\s*([^\s<]+)", normalized)
                m_l = re.search(r"地方\s*獲得?賞金\s*[:：]?\s*([^\s<]+)", normalized)
                if m_c and central is None:
                    central = to_yen(m_c.group(1)) or central
                if m_l and local is None:
                    local = to_yen(m_l.group(1)) or local
            except Exception:
                pass

        # 合算（総が無ければ中央+地方の和）
        if total is None:
            if central is not None or local is not None:
                total = (central or 0) + (local or 0)

        result["central_prize_money"] = central
        result["local_prize_money"] = local
        result["total_prize_money"] = total

        # 最終更新日らしき表記（例: "賞金更新: 2024/05/01", "最終更新 2024-05-01" など）
        m_date = re.search(r"(賞金更新|最終更新)[^0-9]*(\d{4}[/-]\d{1,2}[/-]\d{1,2})", text)
        if m_date:
            y, m, d = re.split(r"[/-]", m_date.group(2))
            result["last_prize_update"] = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
    except Exception:
        # 例外は握りつぶし、Noneのまま返す
        pass
    return result


def _clean_horse_name(name: str) -> str:
    normalized = name.replace("\xa0", " ").replace("\u3000", " ")
    if "※" in normalized:
        normalized = normalized.split("※", 1)[0]
    match = re.match(r"^.*?の[0-9０-９]+", normalized)
    if match:
        return match.group(0).strip()
    parts = re.split(r"[\s\u3000]+", normalized.strip())
    return parts[0] if parts else normalized.strip()


def _detect_broodmare(raw_name: Optional[str]) -> bool:
    if not raw_name:
        return False
    return any(keyword in raw_name for keyword in BROODMARE_KEYWORDS)


def parse_detail_html(
    html: str,
    item_id: int,
    *,
    detail_url: Optional[str] = None,
    fallback_auction_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    soup = BeautifulSoup(html, "html.parser")

    name, raw_name = _extract_name(soup)
    if not name:
        logger.warning("馬名取得に失敗 item_id=%s", item_id)
        return None

    result = DetailParseResult(name=name, auction_id=str(item_id))
    result.raw_name = raw_name or name
    result.is_broodmare = _detect_broodmare(raw_name)
    result.detail_url = detail_url

    # horse info
    try:
        basic_info, detail_info = _horse_info_extractor.extract(soup)
        if basic_info:
            if basic_info.get("sex"):
                result.sex = basic_info["sex"]
            if basic_info.get("age"):
                result.age = basic_info["age"]
            if basic_info.get("sire"):
                result.sire = basic_info["sire"]
            if basic_info.get("dam"):
                result.dam = basic_info["dam"]
            if basic_info.get("damsire"):
                result.dam_sire = basic_info["damsire"]
            if basic_info.get("weight"):
                result.weight = basic_info["weight"]
            if basic_info.get("seller"):
                result.seller = basic_info["seller"]
        if detail_info and detail_info.get("race_record"):
            record = detail_info["race_record"]
            result.race_record = (
                json.dumps(record, ensure_ascii=False) if isinstance(record, dict) else str(record)
            )
    except Exception:
        logger.exception("HorseInfoExtractor.extract failed")

    # HorseInfoExtractor で戦績が取れない場合の補完: 戦績抽出器で HTML から戦績を抽出し、既存の race_record とマージ
    try:
        rr_data, ok = _race_record_extractor.extract(str(soup))
        if ok and rr_data:
            existing_rr = None
            try:
                if result.race_record:
                    existing_rr = json.loads(result.race_record) if isinstance(result.race_record, str) else result.race_record
            except Exception:
                existing_rr = None

            merged: Dict[str, Any] = {}
            if isinstance(existing_rr, dict):
                merged.update(existing_rr)

            # 既存に total_races / wins が無い場合のみ補完（賞金情報などは保持）
            if merged.get("total_races") is None:
                merged["total_races"] = rr_data.get("total_races", 0)
            if merged.get("wins") is None:
                merged["wins"] = rr_data.get("wins", 0)
            if merged.get("record_format") is None:
                merged["record_format"] = rr_data.get("record_format", "simple")
            if rr_data.get("formatted_record") and merged.get("formatted_record") is None:
                merged["formatted_record"] = rr_data.get("formatted_record")

            # race_record が未設定だった場合は rr_data をそのまま使う
            if not merged:
                merged = rr_data

            result.race_record = json.dumps(merged, ensure_ascii=False)
    except Exception:
        logger.exception("RaceRecordExtractor.merge failed")

    if not result.seller:
        try:
            seller_info, ok = _seller_extractor.extract(soup)
            if ok and seller_info:
                result.seller = seller_info.get("seller")
        except Exception:
            logger.exception("Seller extraction failed")

    try:
        price_info, ok = _price_info_extractor.extract(html)
        if ok and price_info:
            result.sold_price = price_info.get("sold_price")
            result.is_unsold = price_info.get("is_unsold", False)
    except Exception:
        logger.exception("PriceInfoExtractor.extract failed")

    if result.sold_price is None:
        price_info = _price_extractor.extract_price(html, result.name)
        result.sold_price = price_info.get("sold_price")
        result.is_unsold = price_info.get("is_unsold", False)

    result.bid_count = _extract_bid_count(html)
    result.bid_count = _extract_bid_count(html)
    if result.bid_count == 0:
        result.is_unsold = True
    elif result.bid_count is not None and result.bid_count > 0:
        # 入札があれば落札されている（主取りではない）とみなす
        result.is_unsold = False

    try:
        comment_data, ok = _comment_extractor.extract(soup)
        if ok and comment_data:
            result.comment = comment_data.get("comment")
            disease = comment_data.get("disease_tags")
            if disease:
                result.disease_tags = disease
    except Exception:
        logger.exception("Comment extraction failed")

    if not result.disease_tags and result.comment:
        try:
            from scripts.components.disease_info_extractor import DiseaseInfoExtractor

            disease_info = DiseaseInfoExtractor(logger=logger.getChild("disease")).extract(
                result.comment
            )
            diseases = disease_info.get("diseases")
            if diseases:
                result.disease_tags = ",".join(diseases)
        except Exception:
            logger.exception("Disease extraction failed")

    result.image_url = _extract_image_url(soup)
    result.jbis_url = _extract_jbis_url(soup)

    # 賞金情報（中央/地方/総）を詳細ページから抽出し、合算を total_prize_start（オークション時点）として反映
    prize_info = _extract_prize_info(html)
    total_prize_money = prize_info.get("total_prize_money")
    
    # 賞金が見つからない場合は0円として扱う（未出走・未勝利など）
    result.total_prize_start = int(total_prize_money) if total_prize_money is not None else 0
    
    # 既存の race_record (JSON文字列) をロード、無ければ初期化
    race_record_payload: Dict[str, Any] = {}
    if result.race_record:
        try:
            rr = json.loads(result.race_record) if isinstance(result.race_record, str) else result.race_record
            if isinstance(rr, dict):
                race_record_payload = rr
        except Exception:
            race_record_payload = {}
    
    # 戦績情報がない場合は「未出走」として初期化
    if not race_record_payload and result.total_prize_start == 0:
        race_record_payload = {
            "total_races": 0,
            "wins": 0,
            "record_format": "simple",
            "formatted_record": "未出走"
        }
            
    # 埋め込み（賞金情報を戦績データにも反映）
    race_record_payload.setdefault("record_format", "simple")
    
    # 賞金情報があれば上書き、なければ0で埋める
    race_record_payload["total_prize_money"] = int(prize_info.get("total_prize_money") or 0)
    if prize_info.get("central_prize_money") is not None:
        race_record_payload["central_prize_money"] = int(prize_info["central_prize_money"])
    if prize_info.get("local_prize_money") is not None:
        race_record_payload["local_prize_money"] = int(prize_info["local_prize_money"])
    if prize_info.get("last_prize_update") is not None:
        race_record_payload["last_prize_update"] = prize_info["last_prize_update"]

    # 反映
    result.race_record = json.dumps(race_record_payload, ensure_ascii=False)

    if not result.auction_date:
        start_time = soup.select_one(".subData__startTime .subData__value")
        if start_time:
            text = start_time.get_text(strip=True)
            m = re.search(r"(\d{4})[年/](\d{1,2})[月/](\d{1,2})日", text)
            if m:
                y, mo, d = m.groups()
                result.auction_date = f"{y}-{int(mo):02d}-{int(d):02d}"
    if not result.auction_date and fallback_auction_date:
        result.auction_date = fallback_auction_date

    return result.to_dict()
