from bs4 import BeautifulSoup
import os

def extract_horse_links(html_file):
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all anchor tags with the specific class
    horse_links = []
    for a_tag in soup.find_all('a', class_='auctionTableCard__name--link'):
        href = a_tag.get('href')
        if href and not href.startswith(('http', '//')):  # Filter out external links
            horse_name = a_tag.get_text(strip=True)
            horse_links.append({
                'name': horse_name,
                'filename': os.path.basename(href)
            })
    
    return horse_links

def save_to_file(links, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for link in links:
            f.write(f"{link['filename']} - {link['name']}\n")

def main():
    # スクリプトの1つ上のディレクトリにあるtest_cacheフォルダ内のHTMLファイルを指定
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(script_dir, 'test_cache', 'fixed_auction_list_updated.html')
    output_file = os.path.join(script_dir, 'test_cache', 'horse_links.txt')
    
    # 入力ファイルが存在するか確認
    if not os.path.exists(input_file):
        print(f"エラー: 入力ファイルが見つかりません: {input_file}")
        print(f"現在の作業ディレクトリ: {os.getcwd()}")
        return
    
    # Extract and save the links
    links = extract_horse_links(input_file)
    save_to_file(links, output_file)
    
    print(f"Found {len(links)} horse links. Results saved to {output_file}")
    
    # Print first few results as a sample
    print("\nSample of extracted links:")
    for link in links[:5]:
        print(f"{link['filename']} - {link['name']}")
    if len(links) > 5:
        print(f"... and {len(links) - 5} more")

if __name__ == "__main__":
    main()
