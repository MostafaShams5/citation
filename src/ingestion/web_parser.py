import trafilatura
import logging

logger = logging.getLogger(__name__)

class WebParser:
    """
    Handles the ingestion and text extraction of web URLs.
    Satisfies the PRD requirement to ignore advertisements and navigational elements.
    """
    
    @staticmethod
    def extract_text(url: str) -> str:
        """
        Downloads a webpage and strips all HTML, CSS, ads, and navigation,
        returning only the core article text.
        """
        logger.info(f"Downloading webpage: {url}")
        
        # Download the raw HTML
        downloaded = trafilatura.fetch_url(url)
        
        if downloaded is None:
            raise Exception(f"Failed to download content from {url}. The site may be blocking bots.")
            
        logger.info("Extracting core text and ignoring advertisements/navbars...")
        
        # Extract the main text, ignoring boilerplate
        main_text = trafilatura.extract(downloaded, include_comments=False, include_tables=False)
        
        if not main_text:
            raise Exception(f"Could not extract meaningful article text from {url}.")
            
        return main_text
