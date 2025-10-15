import unittest

from scripts.components.auction_date_extractor import AuctionDateExtractor


class TestAuctionDateExtractorStartTime(unittest.TestCase):
    def setUp(self):
        self.extractor = AuctionDateExtractor()

    def test_extract_from_start_time_block(self):
        html = '''
        <html>
          <body>
            <div class="subData__startTime">
              <span class="subData__label">開始時間</span>
              <span class="subData__value">2025年10月12日 12:00</span>
            </div>
          </body>
        </html>
        '''
        date_str = self.extractor.extract_from_html(html)
        self.assertEqual(date_str, '2025-10-12')

    def test_no_start_time_block_falls_back(self):
        # When no start time block exists, the extractor should fall back to other logic.
        # Provide a generic date in the page text so it can still find a date.
        html = '''
        <html>
          <body>
            <div class="somewhere-else">開催日: 2024年9月3日</div>
          </body>
        </html>
        '''
        date_str = self.extractor.extract_from_html(html)
        self.assertEqual(date_str, '2024-09-03')


if __name__ == '__main__':
    unittest.main()
