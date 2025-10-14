"""
コメント抽出コンポーネント

このモジュールは、BeautifulSoupオブジェクトから馬のコメントを抽出する機能を提供します。
"""

import re
import logging
from typing import Dict, Optional, Any, Tuple, List


class CommentExtractor:
    """馬のコメントを抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, element) -> Tuple[Optional[Dict[str, str]], bool]:
        """BeautifulSoup要素からコメントを抽出する
        
        楽天競馬オークションの詳細ページからコメントを抽出します。
        コメントは通常、ページのメインコンテンツエリアに含まれています。
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                (抽出したコメント情報を含む辞書, 成功したかどうか)
        """
        try:
            self.logger.debug('コメント抽出を開始します')
            
            # デバッグ用にHTMLを保存
            try:
                with open('debug_comment_page.html', 'w', encoding='utf-8') as f:
                    f.write(str(element))
                self.logger.debug('デバッグ用にHTMLを保存しました: debug_comment_page.html')
                
                # デバッグ用にHTMLの構造をログに出力
                self.logger.debug('HTML構造のデバッグ情報:')
                for i, tag in enumerate(element.find_all(True)[:50]):  # 最初の50タグをログに出力
                    self.logger.debug(f'タグ {i+1}: {tag.name} (クラス: {tag.get("class", [])}, ID: {tag.get("id", "なし")})')
                    
            except Exception as e:
                self.logger.debug(f'HTMLの保存に失敗しました: {e}')
            
            # 方法1: 直接コメントを含む可能性のある要素を検索
            comment = self._extract_direct_comment(element)
            if comment:
                return comment, True
                
            # 方法2: メインコンテンツエリアからコメントを抽出
            comment = self._extract_from_main_content(element)
            if comment:
                return comment, True
                
            # 方法3: コメントセクションを検索
            comment = self._find_comment_section(element)
            if comment:
                return comment, True
                
            # 方法4: すべてのテキストノードからコメントを検索
            comment = self._extract_from_all_text(element)
            if comment:
                return comment, True
                
            self.logger.debug('どの方法でもコメントを見つけることができませんでした')
            return None, False
                
        except Exception as e:
            self.logger.error(f'コメントの抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
            
    def _extract_direct_comment(self, element) -> Optional[Dict[str, str]]:
        """直接コメントを含む可能性のある要素を検索"""
        # デバッグ用にHTMLの構造をログに出力
        self.logger.debug('HTML構造のデバッグ情報:')
        for i, tag in enumerate(element.find_all(True)[:50]):  # 最初の50タグをログに出力
            self.logger.debug(f'タグ {i+1}: {tag.name} (クラス: {tag.get("class", [])}, ID: {tag.get("id", "なし")})')
        
        # 1. まずはテキストノードを全て取得して「本馬について」を探す
        all_text_nodes = element.find_all(string=True)
        self.logger.debug(f'見つかったテキストノードの数: {len(all_text_nodes)}')
        
        # 2. 「本馬について」を含むテキストノードを探す
        for i, text_node in enumerate(all_text_nodes):
            if '本馬について' in text_node:
                self.logger.debug(f'「本馬について」を含むテキストノードを発見: {text_node.strip()}')
                
                # 見つかったノードから親要素をたどって、より広いコンテキストを取得
                parent = text_node.parent
                self.logger.debug(f'親要素: {parent.name} (クラス: {parent.get("class", [])}, ID: {parent.get("id", "なし")})')
                
                # 親要素のテキストを取得
                comment_text = parent.get_text('\n', strip=True)
                self.logger.debug(f'親要素のテキスト（長さ: {len(comment_text)}）: {comment_text[:100]}...')
                
                # 「本馬について」の前の部分を削除
                about_index = comment_text.find('本馬について')
                if about_index != -1:
                    comment_text = comment_text[about_index:]
                    
                    # 十分な長さがあるか確認
                    if len(comment_text) > 50:
                        self.logger.debug('「本馬について」セクションからコメントを抽出しました')
                        return {'comment': comment_text}
                
                # 次の数個のテキストノードも含めて確認
                combined_text = comment_text
                for j, next_node in enumerate(all_text_nodes[i+1:i+5], 1):  # 次の4つのノードまで確認
                    next_text = next_node.get_text('\n', strip=True)
                    if next_text and not next_text.isspace():
                        combined_text += '\n' + next_text
                        self.logger.debug(f'次のノード {j} を追加: {next_text[:50]}...')
                
                if len(combined_text) > len(comment_text):
                    self.logger.debug(f'複数ノードを結合してコメントを抽出しました（長さ: {len(combined_text)}文字）')
                    return {'comment': combined_text}
                
                self.logger.debug(f'単一ノードからコメントを抽出しました（長さ: {len(comment_text)}文字）')
                return {'comment': comment_text}
        
        # 3. テーブル内の「本馬について」を検索
        tables = element.find_all('table')
        self.logger.debug(f'見つかったテーブルの数: {len(tables)}')
        
        for i, table in enumerate(tables, 1):
            # テーブル内に「本馬について」が含まれているか確認
            about_cell = table.find(string=re.compile(r'本馬について'))
            if about_cell:
                self.logger.debug(f'テーブル {i} に「本馬について」が見つかりました')
                # テーブル全体のテキストを取得
                comment_text = table.get_text('\n', strip=True)
                
                # 十分な長さがあるか確認
                if len(comment_text) > 50:
                    self.logger.debug(f'テーブル {i} からコメントを抽出しました（長さ: {len(comment_text)}文字）')
                    return {'comment': comment_text}
        
        # 4. 直接テキストを検索（最終手段）
        html_content = str(element)
        start_markers = ['本馬について', '調教で', '南関東で', '父馬は', '母馬は', '競走成績', '総賞金', '獲得賞金']
        
        for marker in start_markers:
            start_idx = html_content.find(marker)
            if start_idx != -1:
                self.logger.debug(f'マーカー「{marker}」が見つかりました。位置: {start_idx}')
                # 開始点から適当な長さ（5000文字）を取得
                comment_text = html_content[start_idx:start_idx + 5000]
                # HTMLタグを削除
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(comment_text, 'html.parser')
                clean_text = soup.get_text('\n', strip=True)
                
                # 十分な長さがあるか確認
                if len(clean_text) > 50:
                    self.logger.debug(f'「{marker}」から直接コメントを抽出しました（長さ: {len(clean_text)}文字）')
                    return {'comment': clean_text}
        
        # 5. デバッグ用にHTMLをファイルに保存
        debug_file = 'debug_comment_page.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        self.logger.debug(f'コメント抽出用のHTMLを {debug_file} に保存しました')
        
        # 2. その他のコメントが含まれている可能性のある要素を検索
        comment_containers = [
            element.find('div', class_='itemDetail__description'),  # 商品説明セクション
            element.find('div', class_='itemDetail__comment'),     # コメントセクション
            element.find('div', class_='itemDetail__text'),        # テキストセクション
            element.find('div', class_='itemDetail__info'),        # 情報セクション
            element.find('div', class_='itemDetail__content'),     # コンテンツセクション
            element.find('div', class_='description'),             # 説明セクション
            element.find('div', class_='comment'),                 # コメントセクション
            element.find('div', class_='text'),                    # テキストセクション
            element.find('div', class_='info'),                    # 情報セクション
            element.find('div', class_='content'),                 # コンテンツセクション
            element.find('pre'),                                   # preタグ内のテキスト
            element.find('div', {'id': 'itemDetail'}),             # 商品詳細セクション
            element.find('div', {'id': 'description'}),            # 説明セクション
            element.find('div', {'id': 'comment'}),                # コメントセクション
            element.find('section'),                               # sectionタグ
            element.find('article'),                               # articleタグ
        ]
        
        for container in filter(None, comment_containers):
            # テキストを取得して前後の空白を削除
            text = container.get_text('\n', strip=True)
            
            # テキストが十分な長さがあるか確認
            if len(text) < 100:  # 短すぎる場合はスキップ
                continue
                
            # コメントとして適切かチェック（特定のキーワードが含まれているか）
            if any(keyword in text for keyword in ['本馬について', '調教', '脚質', '戦績', '南関東', 'レース', '競走馬']):
                # 不要な部分を削除
                lines = self._clean_comment_text(text)
                if lines:
                    comment = '\n'.join(lines)
                    self.logger.debug('直接コメントを抽出しました')
                    return {'comment': comment}
        
        return None
    
    def _extract_from_main_content(self, element) -> Optional[Dict[str, str]]:
        """メインコンテンツエリアからコメントを抽出"""
        # メインコンテンツエリアを探す
        main_content = element.find('main') or element.find('div', class_=lambda x: x and 'content' in x.lower())
        
        if not main_content:
            self.logger.debug('メインコンテンツエリアが見つかりませんでした')
            return None
            
        # メインコンテンツ内のテキストを取得
        text = main_content.get_text('\n', strip=True)
        
        # テキストが十分な長さがあるか確認
        if len(text) >= 100:
            # コメントとして適切かチェック
            if any(keyword in text for keyword in ['本馬について', '調教', '脚質', '戦績', '南関東', 'レース', '競走馬']):
                # 不要な部分を削除
                lines = self._clean_comment_text(text)
                if lines:
                    comment = '\n'.join(lines)
                    self.logger.debug('メインコンテンツからコメントを抽出しました')
                    return {'comment': comment}
        
        return None
    
    def _find_comment_section(self, element) -> Optional[Dict[str, str]]:
        """コメントセクションを検索して抽出"""
        # 1. テーブル内のコメントを検索
        tables = element.find_all('table')
        for table in tables:
            # テーブル内のテキストを取得
            text = table.get_text('\n', strip=True)
            
            # テキストが十分な長さがあり、コメントとして適切か確認
            if 100 < len(text) < 5000:
                # コメントとして適切なキーワードが含まれているか確認
                if any(keyword in text for keyword in ['本馬について', '調教', '脚質', '戦績', '南関東', 'レース', '競走馬']):
                    # 不要な部分を削除
                    lines = self._clean_comment_text(text)
                    if lines:
                        comment = '\n'.join(lines)
                        self.logger.debug('テーブルからコメントを抽出しました')
                        return {'comment': comment}
        
        # 2. 特定のクラス名やIDを持つ要素を検索
        selectors = [
            'div.itemDetail__description', 'div.itemDetail__comment', 'div.itemDetail__text',
            'div.description', 'div.comment', 'div.text', 'div.info', 'div.content',
            'section', 'article', 'div#itemDetail', 'div#description', 'div#comment',
            'div[itemprop="description"]', 'div.detail', 'div.horse-info', 'div.horse-detail'
        ]
        
        for selector in selectors:
            try:
                elements = element.select(selector)
                for elem in elements:
                    text = elem.get_text('\n', strip=True)
                    if 100 < len(text) < 5000:
                        # コメントとして適切なキーワードが含まれているか確認
                        if any(keyword in text for keyword in ['本馬について', '調教', '脚質', '戦績', '南関東', 'レース', '競走馬']):
                            # 不要な部分を削除
                            lines = self._clean_comment_text(text)
                            if lines:
                                comment = '\n'.join(lines)
                                self.logger.debug(f'セレクタ {selector} からコメントを抽出しました')
                                return {'comment': comment}
            except Exception as e:
                self.logger.debug(f'セレクタ {selector} の処理中にエラーが発生しました: {e}')
        
        return None
    
    def _extract_from_all_text(self, element) -> Optional[Dict[str, str]]:
        """すべてのテキストノードからコメントを検索"""
        # すべてのテキストノードを取得
        text_nodes = element.find_all(string=True, recursive=True)
        
        # テキストを結合
        full_text = '\n'.join(node.strip() for node in text_nodes if node.strip())
        
        # コメントとして適切な部分を抽出
        lines = self._clean_comment_text(full_text)
        if lines:
            # コメントを結合して前後の不要な空白や改行を削除
            comment = '\n'.join(lines).strip()
            # 前後のクォーテーションや括弧を削除
            comment = re.sub(r'^[\s\{\}\[\]"\'\\,]+', '', comment)
            comment = re.sub(r'[\s\{\}\[\]"\'\\,]+$', '', comment)
            
            self.logger.debug(f'全テキストからコメントを抽出しました: "{comment}"')
            return {'comment': comment}
            
        return None
    
    def _clean_comment_text(self, text: str) -> List[str]:
        """コメントテキストをクリーンアップ
        
        Args:
            text: クリーンアップするテキスト
            
        Returns:
            クリーンアップされたテキストのリスト
        """
        import re
        import json
        
        # JSON文字列としてパースを試みる
        try:
            data = json.loads(text)
            if isinstance(data, dict) and 'comment' in data:
                text = data['comment']
        except (json.JSONDecodeError, TypeError):
            # JSONでない場合はそのまま処理を続行
            pass
            
        # 前後の不要な記号や空白を削除
        text = text.strip("\n\r\t \u3000")
        
        # 前後の不要な記号を削除
        text = re.sub(r'^[\s\{\}\[\]"\'\\,]+', '', text)  # 先頭の記号
        text = re.sub(r'[\s\{\}\[\]"\'\\,]+$', '', text)  # 末尾の記号
        
        # 改行で分割して各行を処理
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
                
            # 短すぎる行や不要な情報を除外
            if len(line) < 10 or any(x in line for x in ['総賞金', '落札価格', '価格', '円', '万円', '※', '※※']):
                continue
                
            # 前後の不要な文字列を削除
            line = re.sub(r'^[\s\{\}\[\]"\'\\,]+', '', line)
            line = re.sub(r'[\s\{\}\[\]"\'\\,]+$', '', line)
            
            if line:  # 空行でない場合のみ追加
                lines.append(line)
                
        return lines
