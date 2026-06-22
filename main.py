import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, List

from src.schemas import CitationMetadata
from src.ingestion.pdf_parser import PDFParser
from src.ingestion.docx_parser import DocxParser
from src.ingestion.txt_parser import TextParser
from src.ingestion.web_parser import WebParser
from src.extraction.regex_parser import extract_doi_deterministic, extract_arxiv_id_deterministic
from src.verification.crossref import fetch_from_crossref
from src.verification.arxiv import fetch_metadata_from_arxiv
from src.formatting.csl_engine import CSLEngine
from src.export.exporter import CitationExporter
from src.utils.performance import ThresholdValidator
from src.extraction.llm_extractor import LLMExtractor

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class CitationPipeline:
    
    def __init__(self):
        self.csl_engine = CSLEngine()
        self.llm_extractor = None 
        
    def _ingest_file(self, path_obj: Path) -> str:
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {path_obj}")
            
        ext = path_obj.suffix.lower()
        if ext == ".pdf":
            return PDFParser().extract_text(path_obj)
        elif ext == ".docx":
            return DocxParser().extract_text(path_obj)
        elif ext == ".txt":
            return TextParser().extract_text(path_obj)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    def _enrich_with_urls(self, raw_text: str) -> str:
        url_pattern = re.compile(r'https?://[^\s]+')
        urls = url_pattern.findall(raw_text)
        
        enriched_text = [raw_text]
        for url in urls:
            try:
                logger.info(f"Detected URL. Scraping content from: {url}")
                web_content = WebParser.extract_text(url)
                enriched_text.append(f"\n\n--- CONTENT FROM {url} ---\n\n{web_content}")
            except Exception as e:
                logger.warning(f"Failed to extract content from {url}: {e}")
                
        return "\n".join(enriched_text)

    def _extract_metadata(self, raw_text: str) -> CitationMetadata:
        doi = extract_doi_deterministic(raw_text)
        if doi:
            logger.info(f"Deterministic Match: Found DOI {doi}")
            return fetch_from_crossref(doi)
            
        arxiv_id = extract_arxiv_id_deterministic(raw_text)
        if arxiv_id:
            logger.info(f"Deterministic Match: Found arXiv ID {arxiv_id}")
            return fetch_metadata_from_arxiv(arxiv_id)
            
        logger.warning("No deterministic ID found. Falling back to LLM Extraction...")
        
        # Lazy-load the LLM only if a document actually needs it
        if self.llm_extractor is None:
            logger.info("Loading LLM into GPU memory (this will take a moment on first run)...")
            self.llm_extractor = LLMExtractor(model_id="microsoft/Phi-3-mini-4k-instruct")
            
        return self.llm_extractor.extract(raw_text)
            

    def process_single(self, file_path: Path) -> Dict[str, Any]:
        with ThresholdValidator(target_seconds=4.5, process_identifier=f"Pipeline: {file_path.name}"):
            logger.info(f"Starting ingestion phase for {file_path.name}...")
            raw_text = self._ingest_file(file_path)
            
            if file_path.suffix.lower() == ".txt":
                raw_text = self._enrich_with_urls(raw_text)
            
            logger.info("Starting metadata extraction phase...")
            metadata = self._extract_metadata(raw_text)
            
            logger.info("Starting formatting phase...")
            formatted_citations = self.csl_engine.generate_all_citations(metadata)
            
            logger.info("Starting export generation...")
            exports = {
                "bibtex": CitationExporter.to_bibtex(metadata),
                "ris": CitationExporter.to_ris(metadata),
                "markdown": CitationExporter.to_markdown(formatted_citations)
            }
            
            return {
                "metadata": metadata,
                "formatted_citations": formatted_citations,
                "exports": exports
            }

    def process_batch(self, input_dir: str = "inputs", output_dir: str = "outputs") -> None:
        in_path = Path(input_dir)
        out_path = Path(output_dir)
        
        in_path.mkdir(parents=True, exist_ok=True)
        out_path.mkdir(parents=True, exist_ok=True)
        
        target_extensions = {".pdf", ".docx", ".txt"}
        files_to_process = [f for f in in_path.iterdir() if f.is_file() and f.suffix.lower() in target_extensions]
        
        if not files_to_process:
            logger.warning(f"No valid files found in '{input_dir}' directory.")
            return

        logger.info(f"Found {len(files_to_process)} files to process in '{input_dir}'.")
        
        successful_results: List[Dict] = []
        
        for file_path in files_to_process:
            logger.info("=" * 50)
            logger.info(f"Processing: {file_path.name}")
            try:
                results = self.process_single(file_path)
                successful_results.append(results)
                
                file_out_dir = out_path / file_path.stem
                file_out_dir.mkdir(parents=True, exist_ok=True)
                
                with open(file_out_dir / "metadata.json", "w", encoding="utf-8") as f:
                    json.dump(results["metadata"].model_dump(), f, indent=4)
                    
                with open(file_out_dir / "citations.md", "w", encoding="utf-8") as f:
                    f.write(results["exports"]["markdown"])
                    
                with open(file_out_dir / "export.bib", "w", encoding="utf-8") as f:
                    f.write(results["exports"]["bibtex"])
                    
                with open(file_out_dir / "export.ris", "w", encoding="utf-8") as f:
                    f.write(results["exports"]["ris"])
                    
                logger.info(f"Success! Outputs saved to: {file_out_dir}")
                
            except Exception as e:
                logger.error(f"Failed to process {file_path.name}: {str(e)}")

        # Create Master Bibliography
        if successful_results:
            logger.info("Generating Master Compiled Bibliography...")
            master_bib = CitationExporter.compile_master_bibliography(successful_results)
            with open(out_path / "compiled_master_bibliography.md", "w", encoding="utf-8") as f:
                f.write(master_bib)
            logger.info("Batch execution complete. Master bibliography saved.")

if __name__ == "__main__":
    pipeline = CitationPipeline()
    pipeline.process_batch(input_dir="inputs", output_dir="outputs")
