#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションスクレイパー

このスクリプトは、楽天競馬オークションから馬の情報をスクレイピングし、
JBISから追加情報を取得して、構造化されたデータとして保存します。
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

from core.scraper import RakutenScraper, JBISScraper
from core.models.horse import Horse, Sex
from core.models.auction import Auction
from core.utils.logger import setup_logger
from core.utils.data_validator import Validator

# ロガーの設定
logger = setup_logger(__name__)

class HorseAuctionScraper:
    """馬のオークション情報をスクレイピングするメインクラス"""
    
    def __init__(self, output_dir: str = 'output'):
        """
        初期化
        
        Args:
            output_dir: 出力ディレクトリ
        """
        self.output_dir = output_dir
        self.rakuten_scraper = RakutenScraper()
        self.jbis_scraper = JBISScraper()
        self.validator = Validator()
        
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(self.output_dir, exist_ok=True)
    
    def scrape_horse_list(self, url: str) -> List[Dict]:
        """
        馬の一覧をスクレイピングする
        
        Args:
            url: 馬一覧ページのURL
            
        Returns:
            List[Dict]: 馬の基本情報のリスト
        """
        logger.info(f"馬一覧のスクレイピングを開始します: {url}")
        
        try:
            # 楽天オークションから馬の一覧を取得
            horses = self.rakuten_scraper.fetch_horse_list(url)
            logger.info(f"{len(horses)}件の馬情報を取得しました")
            
            # 結果を保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f'horses_{timestamp}.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            
            logger.info(f"馬一覧を保存しました: {output_file}")
            return horses
            
        except Exception as e:
            logger.error(f"馬一覧のスクレイピング中にエラーが発生しました: {str(e)}")
            raise
    
    def scrape_horse_detail(self, url: str) -> Dict:
        """
        馬の詳細情報をスクレイピングする
        
        Args:
            url: 馬詳細ページのURL
            
        Returns:
            Dict: 馬の詳細情報
        """
        logger.info(f"馬詳細のスクレイピングを開始します: {url}")
        
        try:
            # 楽天オークションから馬の詳細情報を取得
            rakuten_data = self.rakuten_scraper.fetch_horse_detail(url)
            
            # JBISから追加情報を取得（馬IDが利用可能な場合）
            horse_id = self._extract_horse_id(rakuten_data.get('horse', {}).get('name', ''))
            if horse_id:
                try:
                    jbis_data = self.jbis_scraper.fetch_horse_info(horse_id)
                    # 楽天のデータにJBISの情報をマージ
                    if 'horse' in rakuten_data and jbis_data:
                        rakuten_data['horse'].update(jbis_data)
                except Exception as e:
                    logger.warning(f"JBISからの情報取得に失敗しました: {str(e)}")
            
            # 結果を保存
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = os.path.join(self.output_dir, f'horse_detail_{timestamp}.json')
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(rakuten_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"馬詳細を保存しました: {output_file}")
            return rakuten_data
            
        except Exception as e:
            logger.error(f"馬詳細のスクレイピング中にエラーが発生しました: {str(e)}")
            raise
    
    def _extract_horse_id(self, horse_name: str) -> Optional[str]:
        """
        馬名から馬IDを抽出する（必要に応じて実装）
        
        Args:
            horse_name: 馬名
            
        Returns:
            Optional[str]: 馬ID（抽出できない場合はNone）
        """
        # ここに馬名から馬IDを抽出するロジックを実装
        # 例: データベースやマッピングから検索するなど
        return None

def parse_arguments():
    """コマンドライン引数をパースする"""
    parser = argparse.ArgumentParser(description='楽天競馬オークションスクレイパー')
    
    subparsers = parser.add_subparsers(dest='command', help='利用可能なコマンド')
    
    # 馬一覧を取得するコマンド
    list_parser = subparsers.add_parser('list', help='馬の一覧を取得する')
    list_parser.add_argument('url', help='馬一覧ページのURL')
    list_parser.add_argument('-o', '--output', default='output', help='出力ディレクトリ')
    
    # 馬詳細を取得するコマンド
    detail_parser = subparsers.add_parser('detail', help='馬の詳細情報を取得する')
    detail_parser.add_argument('url', help='馬詳細ページのURL')
    detail_parser.add_argument('-o', '--output', default='output', help='出力ディレクトリ')
    
    return parser.parse_args()

def main():
    """メイン関数"""
    try:
        # コマンドライン引数をパース
        args = parse_arguments()
        
        # スクレイパーのインスタンスを作成
        scraper = HorseAuctionScraper(output_dir=args.output)
        
        # コマンドに応じて処理を実行
        if args.command == 'list':
            scraper.scrape_horse_list(args.url)
        elif args.command == 'detail':
            scraper.scrape_horse_detail(args.url)
        else:
            print("有効なコマンドを指定してください。")
            print("利用可能なコマンド: list, detail")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("処理を中断しました")
        sys.exit(0)
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
