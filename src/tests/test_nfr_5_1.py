import sys
import unittest
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from src.ingestion.txt_parser import TextParser
from src.extraction.regex_parser import extract_doi_deterministic
from src.utils.performance import ThresholdValidator

class TestNFRPerformance(unittest.TestCase):
    def setUp(self) -> None:
        self.threshold = 4.5
        self.synthetic_page = "Lorem ipsum dolor sit amet. " * 500
        self.target_text = "\n".join([self.synthetic_page for _ in range(15)])
        self.target_text += "\nFinal reference DOI: 10.1109/CVPR.2016.90"

    def test_parsing_and_extraction_time(self) -> None:
        parser = TextParser()
        
        with ThresholdValidator(self.threshold, "Automated_NFR_Test") as validator:
            raw_text = parser.extract_text(self.target_text)
            extracted_doi = extract_doi_deterministic(raw_text)
            
        self.assertIsNotNone(extracted_doi)
        self.assertEqual(extracted_doi, "10.1109/CVPR.2016.90")
        
        self.assertLessEqual(
            validator.execution_time, 
            self.threshold, 
            f"Execution time {validator.execution_time:.4f}s exceeded {self.threshold}s limit."
        )

if __name__ == '__main__':
    unittest.main()
