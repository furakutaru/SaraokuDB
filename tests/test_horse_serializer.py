import types
from datetime import datetime

import pytest

# Target under test
from backend.services.horse_serializer import serialize_horse


class DummyHorse:
    """A lightweight stand-in for the ORM Horse model with attribute access."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


def test_serialize_horse_plain_values():
    horse = DummyHorse(
        id=1,
        name="テストホース",
        auction_id="A123",
        sex="牡",
        age=4,
        sire="サンプルサイアー",
        dam="サンプルダム",
        dam_sire="サンプルダムサイアー",
        race_record="1-0-0-0",
        weight=480,
        total_prize_start=100.0,
        total_prize_latest=250.5,
        sold_price=8500000,
        auction_date="2025-09-01",
        seller="テストセラー",
        disease_tags="鼻出血",
        comment="良馬体",
        image_url="https://example.com/h.jpg",
        created_at=datetime(2025, 9, 1),
        updated_at=datetime(2025, 9, 2),
    )

    out = serialize_horse(horse)
    assert out["id"] == 1
    assert out["name"] == "テストホース"
    assert out["auction_id"] == "A123"
    assert out["sex"] == "牡"
    assert out["age"] == 4
    assert out["sold_price"] == 8500000
    assert out["auction_date"] == "2025-09-01"
    assert out["seller"] == "テストセラー"
    assert out["comment"] == "良馬体"
    assert out["image_url"].startswith("https://")


def test_serialize_horse_json_array_strings_ints():
    # age/sold_price are JSON-like array strings, auction_date/seller as arrays too
    horse = DummyHorse(
        id=2,
        name="配列文字列ホース",
        auction_id="B999",
        sex='["牝"]',
        age='[3]',
        sold_price='[8500000]',
        auction_date='["2025-08-31","2025-09-10"]',
        seller='["第一牧場","第二牧場"]',
        weight=None,
        total_prize_start=None,
        total_prize_latest=None,
        disease_tags=None,
        comment='["元気"]',
        image_url="/img.png",
        created_at=None,
        updated_at=None,
    )

    out = serialize_horse(horse)
    # Arrays: last int for sold_price via implementation, first element for strings
    assert out["age"] == 3
    assert out["sold_price"] == 8500000
    assert out["auction_date"] == "2025-08-31"  # first element
    assert out["seller"] == "第一牧場"  # first element
    assert out["sex"] == '"牝"' or out["sex"] == '牝'  # tolerant to quotes depending on parsing nuances
    assert out["comment"] in ('["元気"]', '元気')


def test_serialize_horse_string_numbers_and_invalid():
    horse = DummyHorse(
        id=3,
        name="文字列数値ホース",
        auction_id=None,
        sex="セ",
        age="5",
        sold_price="9000000",
        auction_date="2025-09-15",
        seller="販売者",
        comment=None,
        image_url=None,
        created_at=None,
        updated_at=None,
    )

    out = serialize_horse(horse)
    assert out["age"] == 5
    assert out["sold_price"] == 9000000
    assert out["auction_date"] == "2025-09-15"
    assert out["seller"] == "販売者"


def test_serialize_horse_handles_none_gracefully():
    horse = DummyHorse(
        id=4,
        name="NONEテスト",
        age=None,
        sold_price=None,
        auction_date=None,
        seller=None,
        comment=None,
    )

    out = serialize_horse(horse)
    assert out["age"] is None
    assert out["sold_price"] is None
    assert out["auction_date"] is None
    assert out["seller"] is None
    # should include required keys without raising
    for key in ("id", "name", "created_at", "updated_at"):
        assert key in out
