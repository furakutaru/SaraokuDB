import requests
from bs4 import BeautifulSoup

name = 'クレテイユ'
query = f'{name} サラブレッドオークション'
url = f'https://www.google.com/search?q={requests.utils.quote(query)}'

r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
with open('scripts/test_single_google_search.html', 'w', encoding='utf-8') as f:
    f.write(r.text)

soup = BeautifulSoup(r.text, 'html.parser')
results = []
for item in soup.select('div.yuRUbf > a'):
    title = item.get_text()
    link = item.get('href')
    results.append({'title': title, 'url': link})

print(results) 