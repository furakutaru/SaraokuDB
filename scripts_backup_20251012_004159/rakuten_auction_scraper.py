#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションのスクレイパークラス
"""
from pathlib import Path
from typing import Optional, Union, Dict, Any

from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig

class RakutenAuctionScraper(ImprovedRakutenScraper):
    """後方互換性のためのラッパークラス。
    improved_scraper.py の ImprovedRakutenScraper を RakutenAuctionScraper として利用可能にします。
    """
    def __init__(self, data_dir: str = 'static-frontend/public/data'):
        # 親クラスの初期化
        config = ScraperConfig()
        super().__init__(config)
        
        # データディレクトリの設定
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 互換性のための設定
        self.base_url = "https://auction.keiba.rakuten.co.jp/"

    def scrape_all_horses(self, auction_date: str = None):
        """
        互換性のためのメソッド。
        ImprovedRakutenScraper の scrape_horses メソッドを呼び出します。
        """
        return self.scrape_horses(auction_date=auction_date)
