#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークション 過去データサルベージスクリプト（個別ページ巡回）

- item/{id} を巡回して馬名などを取得
- 現行仕様の HorseService を用いてDB保存（name, auction_id を最低限保存）
- 可能な範囲で追加情報（sex, age, など）も取得（未取得でも動作可）

使い方例:
  python scripts/salvage/salvage_rakuten_items.py --start-id 1000 --end-id 1200 --sleep 0.5
  python scripts/salvage/salvage_rakuten_items.py --ids-file ids.txt --dry-run
"""

import os
import re
import sys
import time
import argparse
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests
from bs4 import BeautifulSoup

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# backend 依存の読み込み
from backend.database.models import SessionLocal  # DATABASE_URL 必須
from backend.services.horse_service import HorseService

BASE_URL = "https://auction.keiba.rakuten.co.jp/item/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}


def clean_horse_name(full_name: str) -> str:
    """legacyスクリプトと同等の馬名クリーニングを実施"""
    if not full_name:
        return ""

    # NBSPなどを半角スペースに正規化
    normalized = (
        full_name
        .replace("\xa0", " ")
        .replace("\u3000", " ")
    )

    # 「※」以降の注釈を落とす
    if "※" in normalized:
        normalized = normalized.split("※", 1)[0]

    # 「〜の23」などのパターンが含まれる場合はそこまでを採用
    match = re.match(r"^.*?の[0-9０-９]+", normalized)
    if match:
        return match.group(0).strip()

    # 先頭の単語（半角／全角スペースまで）を取得
    parts = re.split(r"[\s\u3000]+", normalized.strip())
    if parts:
        return parts[0]

    return normalized.strip()

def fetch_item_page(item_id: int) -> Optional[str]:
    url = f"{BASE_URL}{item_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.text
    except Exception:
        return None


def parse_horse_from_html(html: str, item_id: int) -> Optional[Dict[str, Any]]:
    """最小限、現行HorseServiceで保存可能な形へ整形。
    必須: name, auction_id
    取得できない情報は空でOK。
    """
    soup = BeautifulSoup(html, "html.parser")

    # 馬名（商品名）
    name_span = soup.find("span", attrs={"itemprop": "name"})
    if not name_span:
        return None
    raw_name = name_span.get_text(strip=True)
    name = clean_horse_name(raw_name)
    if not name or len(name) < 2:
        return None

    # ここでは最低限の項目に留める（詳細解析は後続で拡張可能）
    horse: Dict[str, Any] = {
        "name": name,
        "auction_id": str(item_id),
        # 以下オプション項目（未取得でも可）
        # 現行の同一馬マージロジックは name 基準を併用しているため、最低限 name + auction_id を保存
        # 必要に応じて auction_date 等のフィールドを将来追加
    }

    # 性別/年齢など、HTML内に分かりやすい箇所があれば追加抽出（暫定: 未取得）
    # 例: 詳細テーブルから取得する場合はここで soup.select(...) を実装

    return horse


def save_horse_via_service(service: HorseService, horse_data: Dict[str, Any]) -> bool:
    db = SessionLocal()
    try:
        # 既存馬の更新/新規保存は HorseService 側に委譲
        service.create_horse(db, horse_data)
        return True
    except Exception:
        db.rollback()
        return False
    finally:
        db.close()


def iter_ids(args) -> List[int]:
    if args.ids_file:
        p = Path(args.ids_file)
        ids: List[int] = []
        if p.exists():
            for line in p.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                if line.isdigit():
                    ids.append(int(line))
        return ids
    # range 指定
    if args.start_id is None or args.end_id is None:
        raise SystemExit("--start-id と --end-id を指定するか、--ids-file を指定してください")
    if args.end_id < args.start_id:
        raise SystemExit("--end-id は --start-id 以上である必要があります")
    return list(range(args.start_id, args.end_id + 1))


def main():
    parser = argparse.ArgumentParser(description="楽天競馬オークション 個別ページサルベージ")
    parser.add_argument("--start-id", type=int, default=None)
    parser.add_argument("--end-id", type=int, default=None)
    parser.add_argument("--ids-file", type=str, default=None, help="巡回するIDを1行1IDで記載したファイル")
    parser.add_argument("--sleep", type=float, default=0.6, help="各リクエスト間のスリープ秒数")
    parser.add_argument("--max-empty", type=int, default=50, help="連続で空ページが続いた場合の打ち切り閾値")
    parser.add_argument("--dry-run", action="store_true", help="保存せずに抽出のみ行う")
    args = parser.parse_args()

    # 前提: DATABASE_URL が環境変数で設定済み（backend.database.models 参照）

    service = HorseService()
    empty_run = 0

    ids = iter_ids(args)
    total = len(ids)

    found = saved = 0
    for i, item_id in enumerate(ids, 1):
        html = fetch_item_page(item_id)
        if not html:
            empty_run += 1
            if empty_run >= args.max_empty:
                print(f"[INFO] 空ページが {empty_run} 回連続したため打ち切り: item_id={item_id}")
                break
            time.sleep(args.sleep)
            continue

        empty_run = 0
        horse = parse_horse_from_html(html, item_id)
        if not horse:
            time.sleep(args.sleep)
            continue

        found += 1
        if args.dry_run:
            print(f"[DRY] {found}/{total} name={horse['name']} auction_id={horse['auction_id']}")
        else:
            ok = save_horse_via_service(service, horse)
            if ok:
                saved += 1
                print(f"[OK]  {saved}/{found} name={horse['name']} auction_id={horse['auction_id']}")
            else:
                print(f"[NG]  name={horse['name']} auction_id={horse['auction_id']}")

        time.sleep(args.sleep)

    print(f"[DONE] 抽出:{found} / 保存:{saved}")


if __name__ == "__main__":
    main()
