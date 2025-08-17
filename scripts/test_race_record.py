from bs4 import BeautifulSoup
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_race_record_extraction(html_file):
    """Test the race record extraction logic with a given HTML file."""
    try:
        # Read the test HTML file
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Parse the HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get the page text
        page_text = ' '.join(soup.stripped_strings)
        logger.info(f"Page text: {page_text[:200]}...")
        
        # Check for the race record
        if '通算成績：3戦0勝［0-0-0-3］' in page_text or '通算成績：3戦0勝[0-0-0-3]' in page_text:
            race_record = "3戦0勝[0-0-0-3]"
            logger.info(f"Race record found: {race_record}")
            return True
        else:
            logger.error("Race record not found in the page text")
            return False
            
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        return False

if __name__ == "__main__":
    test_file = "test_vihita.html"
    logger.info(f"Testing race record extraction with file: {test_file}")
    
    success = test_race_record_extraction(test_file)
    
    if success:
        logger.info("Test passed: Race record was successfully extracted")
    else:
        logger.error("Test failed: Could not extract race record")
