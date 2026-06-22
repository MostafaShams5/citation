# src/ingestion/pdf_parser.py

import fitz  # PyMuPDF
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class DocumentParsingError(Exception):
    """Custom exception raised when document extraction fails."""
    pass

class PDFParser:
    """
    Handles the ingestion and text extraction of PDF documents.
    Adheres to the Single Responsibility Principle.
    """
    
    def __init__(self, max_pages: int = 15):
        """
        Initialize the parser.
        :param max_pages: NFR 5.1 dictates optimization for up to 15 pages.
        """
        self.max_pages = max_pages

    def extract_text(self, file_path: str | Path) -> str:
        """
        Extracts raw text from a given PDF file path.
        
        :param file_path: Path to the .pdf file
        :return: A single string containing the extracted text.
        :raises DocumentParsingError: If the file cannot be read or is corrupted.
        """
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"The file {path_obj.name} does not exist.")
            
        if path_obj.suffix.lower() != '.pdf':
            raise ValueError(f"Expected a PDF file, got {path_obj.suffix}")

        extracted_text = []
        
        try:
            logger.info(f"Opening {path_obj.name} for text extraction...")
            # Open the document safely using a context manager
            with fitz.open(path_obj) as doc:
                # Limit parsing to the maximum allowed pages to guarantee < 4.5s processing
                pages_to_parse = min(len(doc), self.max_pages)
                
                for page_num in range(pages_to_parse):
                    page = doc.load_page(page_num)
                    # Extract text blocks, preserving basic document flow
                    text = page.get_text("text")
                    if text.strip():
                        extracted_text.append(text)
                        
            logger.info(f"Successfully extracted {len(extracted_text)} pages of text.")
            
            # Join pages with a clear delimiter so the LLM understands page breaks
            return "\n\n--- PAGE BREAK ---\n\n".join(extracted_text)

        except Exception as e:
            logger.error(f"Failed to parse PDF: {str(e)}")
            raise DocumentParsingError(f"Error parsing {path_obj.name}: {str(e)}") from e

# ==========================================
# TEST BLOCK (To run your real input data)
# ==========================================
if __name__ == "__main__":

    
    test_file_path = "2504.04050v3.pdf" 
    
    parser = PDFParser()
    try:
        raw_text = parser.extract_text(test_file_path)
        print("\n--- EXTRACTED TEXT PREVIEW (First 1000 characters) ---")
        print(raw_text[:100000])
        print("------------------------------------------------------")
    except Exception as e:
        print(f"Test failed: {e}")
