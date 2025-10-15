from bs4 import BeautifulSoup
import re

# Sample HTML that mimics the JBIS page structure
sample_html = """
<div class="data-4__item-2">
    <dt>総賞金</dt>
    <dd>1,234.5万円</dd>
</div>
"""

def test_prize_extraction(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Method 1: Search by class name
    for div in soup.find_all('div', class_='data-4__item-2'):
        dt = div.find('dt')
        if dt and '総賞金' in dt.get_text(strip=True):
            dd = div.find('dd')
            if dd:
                prize_text = dd.get_text(strip=True)
                print(f"Found prize text: {prize_text}")
                
                # Extract the numeric value
                prize_text = prize_text.replace(' ', '').replace('\u3000', '').replace('万円', '')
                match = re.search(r'([\d,]+(?:\.[\d,]+)?)', prize_text)
                if match:
                    total_prize = float(match.group(1).replace(',', ''))
                    print(f"Extracted prize: {total_prize}万円")
                    return total_prize
    
    print("Prize not found")
    return 0.0

# Run the test
prize = test_prize_extraction(sample_html)
print(f"Final result: {prize}万円")
