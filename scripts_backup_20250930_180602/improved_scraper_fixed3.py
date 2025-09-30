
    def scrape_horse_list(self, url: str = None, use_cache: bool = False) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Args:
            url: スクレイピング対象のURL（Noneの場合はベースURLを使用）
            use_cache: キャッシュを使用するかどうか
            
        Returns:
            List[Dict[str, Any]]: 馬情報のリスト
        """
        if self.test_mode:
            self.logger.info("テストモード: サンプルデータを返します")
            return [
                {
                    "id": "test1",
                    "name": "テスト馬1",
                    "sire": "テスト父",
                    "dam": "テスト母",
                    "damsire": "テスト母父",
                    "sex": "牡",
                    "age": 3,
                    "seller": "テスト牧場",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/1"
                },
                {
                    "id": "test2",
                    "name": "テスト馬2",
                    "sire": "テスト父2",
                    "dam": "テスト母2",
                    "damsire": "テスト母父2",
                    "sex": "牝",
                    "age": 2,
                    "seller": "テスト牧場2",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/2"
                },
                {
                    "id": "test3",
                    "name": "テスト馬3",
                    "sire": "テスト父3",
                    "dam": "テスト母3",
                    "damsire": "テスト母父3",
                    "sex": "セ",
                    "age": 4,
                    "seller": "テスト牧場3",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/3"
                }
            ]
            
        # 実際のスクレイピング処理を呼び出す
        return self._scrape_horse_list(url=url, use_cache=use_cache)
