"""
HTML要素から最適なセレクタを生成するユーティリティ
"""
from typing import List, Dict, Optional, Tuple
from bs4 import Tag, BeautifulSoup
import re

class SelectorFinder:
    @staticmethod
    def find_best_selectors(html_content: str, target_texts: List[str]) -> Dict[str, List[str]]:
        """
        HTML内から特定のテキストを含む要素を見つけ、最適なセレクタを返す
        
        Args:
            html_content: 解析対象のHTML
            target_texts: 検索するテキストのリスト（例: ["牡", "牝", "セ", "歳"]）
            
        Returns:
            Dict[str, List[str]]: テキストをキーとし、見つかったセレクタのリストを値とする辞書
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result = {text: [] for text in target_texts}
        
        # すべての要素を走査
        for element in soup.find_all(True):
            if not element.text.strip():
                continue
                
            # 要素のテキストを取得
            element_text = element.get_text(strip=True)
            
            # 各ターゲットテキストに対してチェック
            for text in target_texts:
                if text in element_text:
                    # セレクタを生成
                    selector = SelectorFinder._generate_selector(element)
                    if selector:
                        result[text].append(selector)
        
        return result
    
    @staticmethod
    def _generate_selector(element: Tag) -> Optional[str]:
        """要素から最適なセレクタを生成する"""
        # クラスベースのセレクタを試す
        if element.get('class'):
            # クラス名に数字だけのものは避ける
            valid_classes = [c for c in element['class'] if not c.isdigit()]
            if valid_classes:
                # クラス名が複数ある場合は、より具体的なセレクタを生成
                return f".{'.'.join(valid_classes)}"
        
        # idベースのセレクタ
        if element.get('id'):
            return f"#{element['id']}"
            
        # 要素名 + 属性の組み合わせ
        attrs = []
        for attr in ['name', 'type', 'role', 'aria-label']:
            if element.get(attr):
                attrs.append(f"[{attr}='{element[attr]}']")
                
        if attrs:
            return f"{element.name}{''.join(attrs)}"
            
        # 親要素を考慮したセレクタ
        parent = element.parent
        if parent and parent.name != '[document]':
            parent_selector = SelectorFinder._generate_selector(parent)
            if parent_selector:
                return f"{parent_selector} > {element.name}"
        
        # 単純な要素名
        return element.name if element.name else None

    @staticmethod
    def find_common_patterns(selectors: List[str]) -> List[str]:
        """
        セレクタのリストから共通パターンを見つける
        """
        if not selectors:
            return []
            
        # クラス名の出現回数をカウント
        class_counts = {}
        for selector in selectors:
            classes = re.findall(r'\.([^\s\.\[\]\#:]+)', selector)
            for cls in classes:
                class_counts[cls] = class_counts.get(cls, 0) + 1
        
        # 2回以上出現するクラスを共通パターンとして抽出
        common_classes = [cls for cls, count in class_counts.items() if count > 1]
        
        # 共通クラスを使用したセレクタを生成
        common_selectors = []
        if common_classes:
            common_selectors.append(f".{'.'.join(common_classes)}")
            
        return common_selectors

def main():
    # 使用例
    with open('path/to/your/html_file.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 検索したいテキスト（性別や年齢に関連するテキスト）
    target_texts = ["牡", "牝", "セ", "歳"]
    
    # セレクタを検索
    finder = SelectorFinder()
    selectors = finder.find_best_selectors(html_content, target_texts)
    
    # 結果を表示
    for text, found_selectors in selectors.items():
        print(f"\n'{text}' を含む要素のセレクタ:")
        for selector in found_selectors:
            print(f"  - {selector}")
        
        # 共通パターンを抽出
        common = finder.find_common_patterns(found_selectors)
        if common:
            print("\n  共通パターン:")
            for pattern in common:
                print(f"  - {pattern}")

if __name__ == "__main__":
    main()
