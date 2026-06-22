import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TextParser:
    """
    Handles the ingestion of raw .txt files and raw string text snippets.
    """
    
    def extract_text(self, input_data: str | Path) -> str:
        """
        Checks if the input is a valid file path to a .txt file. 
        If it is, reads the file. If it isn't, assumes the input IS the raw text itself.
        """
        try:
            # Try to evaluate if input is a valid file path
            path_obj = Path(input_data)
            if path_obj.is_file() and path_obj.suffix.lower() == '.txt':
                logger.info(f"Reading text file: {path_obj.name}")
                with open(path_obj, 'r', encoding='utf-8') as f:
                    return f.read()
        except OSError:
            # If path validation fails (e.g., string is too long to be a path), pass gracefully
            pass

        # If it's not a file path, treat the input as a raw text snippet (Inline Editor feature)
        logger.info("Processing input as raw inline text snippet...")
        if not input_data.strip():
            raise ValueError("Provided text input is empty.")
            
        return input_data
