def _extract_seller(self, page_text: str) -> str:
    """Extract seller information from page text.
    
    Args:
        page_text (str): The page text to extract from.
        
    Returns:
        str: The extracted seller name, or empty string if not found.
    """
    try:
        # Method 1: Direct regex search
        seller_match = re.search(r'販売申込者[：:]([^\n\r\t]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            # Remove everything after "（" and return
            return re.sub(r'（.*$', '', seller).strip()
        
        # Method 2: Extract from table
        soup = BeautifulSoup(page_text, 'html.parser')
        table_rows = soup.find_all('tr')
        for row in table_rows:
            th = row.find('th')
            td = row.find('td')
            if th and td and ('販売申込者' in th.get_text() or 'seller' in th.get_text().lower()):
                seller = td.get_text(strip=True)
                return re.sub(r'（.*$', '', seller).strip()
        
        return ''
        
    except Exception as e:
        print(f"Error extracting seller: {str(e)}")
        return ''
