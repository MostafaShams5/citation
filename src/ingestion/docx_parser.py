import logging
from pathlib import Path
import docx

logger = logging.getLogger(__name__)

class DocxParser:
    """
    Handles the ingestion and text extraction of Microsoft Word (.docx) documents.
    """
    
    def extract_text(self, file_path: str | Path) -> str:
        """
        Extracts raw text from a given .docx file path.
        """
        path_obj = Path(file_path)
        
        if not path_obj.exists():
            raise FileNotFoundError(f"The file {path_obj.name} does not exist.")
            
        if path_obj.suffix.lower() != '.docx':
            raise ValueError(f"Expected a .docx file, got {path_obj.suffix}")

        try:
            logger.info(f"Opening {path_obj.name} for text extraction...")
            doc = docx.Document(path_obj)
            
            # Extract text from paragraphs
            extracted_text = [paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()]
            
            logger.info(f"Successfully extracted {len(extracted_text)} paragraphs of text.")
            
            # Join paragraphs using double newlines for clear LLM/Regex readability
            return "\n\n".join(extracted_text)

        except Exception as e:
            logger.error(f"Failed to parse DOCX: {str(e)}")
            raise Exception(f"Error parsing {path_obj.name}: {str(e)}") from e
