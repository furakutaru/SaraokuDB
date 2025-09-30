import re
from pathlib import Path

def analyze_html(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"File size: {len(content)} bytes")
    
    # Look for common patterns
    print("\nCommon tags in the file:")
    tags = re.findall(r'<(\w+)', content[:5000])  # Check first 5000 chars
    tag_counts = {}
    for tag in tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    print(sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10])
    
    # Look for potential horse information
    print("\nPotential horse names (text after <title>):")
    titles = re.findall(r'<title>([^<]+)</title>', content)
    for title in titles[:5]:
        print(f"  - {title}")
    
    # Look for URLs that might contain horse details
    print("\nPotential detail page URLs:")
    urls = re.findall(r'href=["\']([^"\']+/item/[^"\']+)["\']', content)
    for url in urls[:5]:
        print(f"  - {url}")

if __name__ == "__main__":
    file_path = "/Users/yum.ishii/SaraokuDB/cache/202508161516/list.html"
    analyze_html(file_path)
