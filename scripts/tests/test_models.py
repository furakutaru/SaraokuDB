"""
モデルクラスのユニットテスト
"""
import unittest
from datetime import datetime

from core.models.horse import Horse, Sex
from core.models.auction import Auction

class TestHorseModel(unittest.TestCase):
    """Horseモデルのテスト"""
    
    def test_horse_creation(self):
        """Horseオブジェクトの作成テスト"""
        horse = Horse(
            name="テスト馬",
            sex=Sex.MALE,
            age=3,
            sire="テスト父",
            dam="テスト母",
            damsire="テスト母父",
            total_prize=1000.5,
            race_record="10-3-2-1",
            comment="テストコメント"
        )
        
        self.assertEqual(horse.name, "テスト馬")
        self.assertEqual(horse.sex, Sex.MALE)
        self.assertEqual(horse.age, 3)
        self.assertEqual(horse.sire, "テスト父")
        self.assertEqual(horse.dam, "テスト母")
        self.assertEqual(horse.damsire, "テスト母父")
        self.assertEqual(horse.total_prize, 1000.5)
        self.assertEqual(horse.race_record, "10-3-2-1")
        self.assertEqual(horse.comment, "テストコメント")
    
    def test_to_dict(self):
        """to_dictメソッドのテスト"""
        horse = Horse(
            name="テスト馬",
            sex=Sex.FEMALE,
            age=4,
            sire="テスト父",
            dam="テスト母",
            damsire="テスト母父"
        )
        
        horse_dict = horse.to_dict()
        
        self.assertEqual(horse_dict["name"], "テスト馬")
        self.assertEqual(horse_dict["sex"], "牝")
        self.assertEqual(horse_dict["age"], 4)
        self.assertEqual(horse_dict["sire"], "テスト父")
        self.assertEqual(horse_dict["dam"], "テスト母")
        self.assertEqual(horse_dict["damsire"], "テスト母父")
        self.assertIsNone(horse_dict["total_prize"])
        self.assertIsNone(horse_dict["race_record"])
        self.assertIsNone(horse_dict["comment"])
    
    def test_from_dict(self):
        """from_dictメソッドのテスト"""
        horse_data = {
            "name": "テスト馬",
            "sex": "牡",
            "age": 5,
            "sire": "テスト父",
            "dam": "テスト母",
            "damsire": "テスト母父",
            "total_prize": 2000.0,
            "race_record": "20-5-3-2",
            "comment": "テストコメント"
        }
        
        horse = Horse.from_dict(horse_data)
        
        self.assertEqual(horse.name, "テスト馬")
        self.assertEqual(horse.sex, Sex.MALE)
        self.assertEqual(horse.age, 5)
        self.assertEqual(horse.sire, "テスト父")
        self.assertEqual(horse.dam, "テスト母")
        self.assertEqual(horse.damsire, "テスト母父")
        self.assertEqual(horse.total_prize, 2000.0)
        self.assertEqual(horse.race_record, "20-5-3-2")
        self.assertEqual(horse.comment, "テストコメント")

class TestAuctionModel(unittest.TestCase):
    """Auctionモデルのテスト"""
    
    def test_auction_creation(self):
        """Auctionオブジェクトの作成テスト"""
        auction = Auction(
            auction_id="A001",
            horse_id="H001",
            auction_date=datetime(2023, 1, 1),
            seller="テスト出品者",
            buyer="テスト落札者",
            price=3000.5,
            is_unsold=False,
            comment="テストコメント",
            metadata={"key": "value"}
        )
        
        self.assertEqual(auction.auction_id, "A001")
        self.assertEqual(auction.horse_id, "H001")
        self.assertEqual(auction.auction_date, datetime(2023, 1, 1))
        self.assertEqual(auction.seller, "テスト出品者")
        self.assertEqual(auction.buyer, "テスト落札者")
        self.assertEqual(auction.price, 3000.5)
        self.assertFalse(auction.is_unsold)
        self.assertEqual(auction.comment, "テストコメント")
        self.assertEqual(auction.metadata, {"key": "value"})
    
    def test_to_dict(self):
        """to_dictメソッドのテスト"""
        auction = Auction(
            auction_id="A001",
            horse_id="H001",
            auction_date=datetime(2023, 1, 1),
            seller="テスト出品者",
            buyer="テスト落札者",
            price=3000.5
        )
        
        auction_dict = auction.to_dict()
        
        self.assertEqual(auction_dict["auction_id"], "A001")
        self.assertEqual(auction_dict["horse_id"], "H001")
        self.assertEqual(auction_dict["auction_date"], "2023-01-01T00:00:00")
        self.assertEqual(auction_dict["seller"], "テスト出品者")
        self.assertEqual(auction_dict["buyer"], "テスト落札者")
        self.assertEqual(auction_dict["price"], 3000.5)
        self.assertFalse(auction_dict["is_unsold"])
        self.assertIsNone(auction_dict["comment"])
        self.assertEqual(auction_dict["metadata"], {})
    
    def test_from_dict(self):
        """from_dictメソッドのテスト"""
        auction_data = {
            "auction_id": "A001",
            "horse_id": "H001",
            "auction_date": "2023-01-01T12:34:56",
            "seller": "テスト出品者",
            "buyer": "テスト落札者",
            "price": 3000.5,
            "is_unsold": False,
            "comment": "テストコメント",
            "metadata": {"key": "value"}
        }
        
        auction = Auction.from_dict(auction_data)
        
        self.assertEqual(auction.auction_id, "A001")
        self.assertEqual(auction.horse_id, "H001")
        self.assertEqual(auction.auction_date, datetime(2023, 1, 1, 12, 34, 56))
        self.assertEqual(auction.seller, "テスト出品者")
        self.assertEqual(auction.buyer, "テスト落札者")
        self.assertEqual(auction.price, 3000.5)
        self.assertFalse(auction.is_unsold)
        self.assertEqual(auction.comment, "テストコメント")
        self.assertEqual(auction.metadata, {"key": "value"})

if __name__ == '__main__':
    unittest.main()
