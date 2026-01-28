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
import sys
import time
import argparse
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

import requests

# プロジェクトルートをPythonパスに追加
PROJECT_ROOT = Path(__file__).parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# backend 依存の読み込み
from backend.database.models import SessionLocal, Horse, AuctionHistory  # DATABASE_URL 必須
from backend.services.horse_service import HorseService

from scripts.rakuten.detail_parser import parse_detail_html

BASE_URL = "https://auction.keiba.rakuten.co.jp/item/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
}


def fetch_item_page(item_id: int) -> Optional[str]:
    url = f"{BASE_URL}{item_id}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 404:
            print(f"[INFO] 404 Not Found: item_id={item_id} url={url}")
            return None
        if resp.status_code != 200:
            print(f"[WARN] HTTP {resp.status_code}: item_id={item_id} url={url}")
        resp.raise_for_status()
        return resp.text
    except requests.exceptions.Timeout:
        print(f"[WARN] Timeout fetching item_id={item_id} url={url}")
        return None
    except Exception as e:
        print(f"[WARN] Error fetching item_id={item_id} url={url}: {e}")
        return None


def parse_horse_from_html(
    html: str,
    item_id: int,
    *,
    detail_url: Optional[str] = None,
    fallback_auction_date: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    return parse_detail_html(
        html,
        item_id,
        detail_url=detail_url,
        fallback_auction_date=fallback_auction_date,
    )


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
        else:
            print(f"[WARN] 指定された ids_file が見つかりません: {p}")
        if not ids:
            print(f"[WARN] ids_file に有効な数値IDが見つかりませんでした: {p}")
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
    parser.add_argument("--auction-date", type=str, default=None, help="未取得時に適用する開催日 (YYYY-MM-DD)")
    parser.add_argument("--update-only", action="store_true", help="更新のみ: 出品履歴に関わるフィールドを更新しない")
    parser.add_argument("--broodmare-only", action="store_true", help="繁殖牝馬のみ保存対象にする")
    args = parser.parse_args()

    # 前提: DATABASE_URL が環境変数で設定済み（backend.database.models 参照）

    service = HorseService()
    empty_run = 0

    ids = iter_ids(args)
    total = len(ids)
    # デバッグ: 読み込んだIDの件数と先頭サンプルを表示
    print(f"[INFO] 読み込んだID件数: {total}")
    if total > 0:
        sample = ids[:10]
        print(f"[INFO] 先頭サンプルID: {sample}")
    else:
        print("[WARN] IDが1件も読み込めませんでした。--ids-file のパスや内容をご確認ください。")

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
        detail_url = f"{BASE_URL}{item_id}"
        horse = parse_horse_from_html(
            html,
            item_id,
            detail_url=detail_url,
            fallback_auction_date=args.auction_date,
        )
        if not horse:
            time.sleep(args.sleep)
            continue

        is_broodmare = bool(horse.get("is_broodmare"))
        if args.broodmare_only and not is_broodmare:
            print(f"[SKIP] Broodmare-only モードのためスキップ: item_id={item_id} name={horse.get('name')}")
            time.sleep(args.sleep)
            continue

        found += 1
        if args.dry_run:
            summary = [
                f"name={horse['name']}",
                f"auction_id={horse['auction_id']}",
            ]
            if horse.get("raw_name"):
                summary.append(f"raw_name={horse['raw_name']}")
            summary.append(f"is_broodmare={is_broodmare}")
            for key in ["sex", "age", "seller", "sold_price", "auction_date", "total_prize_latest", "image_url"]:
                value = horse.get(key)
                if value is not None and value != "":
                    summary.append(f"{key}={value}")
            # race_record 内の賞金系フォールバック値も併記
            rr = horse.get("race_record")
            try:
                if rr:
                    rr_obj = rr if isinstance(rr, dict) else json.loads(rr)
                    for k in ["total_prize_money", "central_prize_money", "local_prize_money", "last_prize_update"]:
                        if isinstance(rr_obj, dict) and k in rr_obj and rr_obj[k] is not None:
                            summary.append(f"race_record.{k}={rr_obj[k]}")
            except Exception:
                pass
            if args.update_only:
                summary.append("mode=update-only")
            print(f"[DRY] {found}/{total} " + " ".join(summary))
        else:
            # --update-only と --broodmare-only が同時指定された場合は賞金更新をスキップ
            if args.update_only and args.broodmare_only:
                print(f"[INFO] Broodmare-only & Update-only モード: 賞金更新をスキップします (item_id={item_id} name={horse.get('name')})")
                # 既存の履歴カラムや出品ステータスに影響しうるキーを除外
                for k in [
                    "auction_date",  # 履歴扱いの可能性
                    "sold_price",    # 価格履歴
                    "is_unsold",     # 主取りステータス
                    "unsold_count",  # 主取り回数
                    "seller",        # 出品者履歴
                    "comment",       # コメント履歴
                    "total_prize_start",  # 賞金履歴
                    "total_prize_latest",  # 賞金履歴
                    "last_prize_update",  # 賞金更新日
                ]:
                    if k in horse:
                        horse.pop(k, None)
            # 更新のみモード: 出品履歴に関わるフィールドを送らない
            # ただし、sold_price と seller は欠損データ補完のため保持
            elif args.update_only:
                # 既存の履歴カラムや出品ステータスに影響しうるキーを除外
                for k in [
                    "auction_date",  # 履歴扱いの可能性
                    "is_unsold",     # 主取りステータス
                    "unsold_count",  # 主取り回数
                    "comment",       # コメント履歴
                ]:
                    if k in horse:
                        horse.pop(k, None)
            # 比較用: 既存データの取得
            db = SessionLocal()
            existing_prize = None
            try:
                h_obj = db.query(Horse).filter(Horse.auction_id == str(item_id)).first()
                if h_obj:
                    existing_prize = h_obj.total_prize_start
            finally:
                db.close()

            # 保存前に total_prize_latest を削除（Keibabookデータを保護）
            horse.pop("total_prize_latest", None)
            
            # 保存
            ok = save_horse_via_service(service, horse)
            if ok:
                saved += 1
                new_prize = horse.get("total_prize_latest") or horse.get("total_prize_start")
                
                try:
                    is_diff = int(float(existing_prize)) != int(float(new_prize)) if existing_prize is not None and new_prize is not None else existing_prize != new_prize
                except Exception:
                    is_diff = str(existing_prize) != str(new_prize)

                msg = f"[OK]  {saved}/{found} name={horse['name']} auction_id={horse['auction_id']}"
                if existing_prize is not None and is_diff:
                    msg += f" [DISCREPANCY!!!] OldPrize={existing_prize} -> NewPrize={new_prize}"
                print(msg)
            else:
                print(f"[NG]  name={horse['name']} auction_id={horse['auction_id']}")

        time.sleep(args.sleep)

    print(f"[DONE] 抽出:{found} / 保存:{saved}")


if __name__ == "__main__":
    main()
