import pytest
from bs4 import BeautifulSoup
from scripts.improved_scraper import ImprovedRakutenScraper

class TestHorseNameSamples:
    @pytest.fixture
    def scraper(self):
        return ImprovedRakutenScraper(test_mode=True)

    def test_sample_horse_names(self, scraper):
        """実際の馬名の例でテスト"""
        test_cases = [
            # 基本パターン
            {
                'html': '<div class="auctionTableCard__name">サクラバクシンオー</div>',
                'expected': 'サクラバクシンオー'
            },
            # 価格表記あり
            {
                'html': '<div class="auctionTableCard__name">キタサンブラック 1,234万円</div>',
                'expected': 'キタサンブラック'
            },
            # 価格表記（カンマなし）
            {
                'html': '<div class="auctionTableCard__name">アーモンドアイ 5000万円</div>',
                'expected': 'アーモンドアイ'
            },
            # 価格表記（小数点あり）
            {
                'html': '<div class="auctionTableCard__name">キタサンブラック 1,234.5万円</div>',
                'expected': 'キタサンブラック'
            },
            # 価格表記（半角スペースなし）
            {
                'html': '<div class="auctionTableCard__name">キタサンブラック1,234万円</div>',
                'expected': 'キタサンブラック'
            },
            # 長い名前
            {
                'html': '<div class="auctionTableCard__name">ミスターシービーインパクト 1,234万円</div>',
                'expected': 'ミスターシービーインパクト'
            },
            # 記号を含む名前
            {
                'html': '<div class="auctionTableCard__name">キタサン-ブラック 1,234万円</div>',
                'expected': 'キタサン-ブラック'
            },
            # 実際の省略例
            {
                'html': '<div class="auctionTableCard__name">ディープインパクト…</div>',
                'expected': 'ディープインパクト'
            },
            # 実際の例（価格と省略の両方）
            {
                'html': '<div class="auctionTableCard__name">キタサンブラック… 1,234万円</div>',
                'expected': 'キタサンブラック'
            },
            # 複数行の例
            {
                'html': '''<div class="auctionTableCard__name">
                            サクラバクシンオー
                            1,234万円
                        </div>''',
                'expected': 'サクラバクシンオー'
            }
        ]

        for i, test_case in enumerate(test_cases, 1):
            soup = BeautifulSoup(test_case['html'], 'html.parser')
            name_elem = soup.select_one('.auctionTableCard__name')
            result = scraper._clean_horse_name(name_elem)
            print(f"\nテストケース {i}:")
            print(f"入力: {test_case['html']}")
            print(f"期待: {test_case['expected']}")
            print(f"結果: {result}")
            assert result == test_case['expected'], f"テストケース {i} が失敗しました"
