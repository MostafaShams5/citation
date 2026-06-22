import urllib.request
from pathlib import Path
from typing import Any, Optional, Dict

from citeproc import (
    Citation,
    CitationItem,
    CitationStylesBibliography,
    CitationStylesStyle,
    formatter,
)
from citeproc.source.json import CiteProcJSON
from src.schemas import CitationMetadata
from src.formatting.normalizer import CitationNormalizer

class CSLEngine:
    CSL_REPO_BASE = "https://raw.githubusercontent.com/citation-style-language/styles/master/"

    STYLES = {
        "APA (7th Ed)": "apa",
        "MLA (9th Ed)": "modern-language-association",
        "Chicago (17th Ed)": "chicago-author-date",
        "Harvard": "harvard-cite-them-right",
        "IEEE": "ieee",
    }

    def __init__(self, style_dir: str = "csl_styles"):
        self.style_dir = Path(__file__).parent / style_dir
        self.style_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_styles_downloaded()

    def _ensure_styles_downloaded(self) -> None:
        for _, style_id in self.STYLES.items():
            file_path = self.style_dir / f"{style_id}.csl"
            if not file_path.exists():
                try:
                    urllib.request.urlretrieve(f"{self.CSL_REPO_BASE}{style_id}.csl", file_path)
                except Exception:
                    pass

    @staticmethod
    def _clean_text(value: Optional[str]) -> Optional[str]:
        if not value:
            return None
        return value.strip().rstrip(".") or None

    def _determine_csl_type(self, metadata: CitationMetadata) -> str:
        if self._clean_text(getattr(metadata, "container_title", None)):
            return "article-journal"
        if getattr(metadata, "doi", None):
            return "article-journal"
        if self._clean_text(getattr(metadata, "publisher", None)):
            return "book"
        return "document"

    def _map_to_csl_json(self, metadata: CitationMetadata) -> list[dict[str, Any]]:
        csl_type = self._determine_csl_type(metadata)
        csl_item: dict[str, Any] = {
            "id": "item-1",
            "type": csl_type,
            "title": self._clean_text(metadata.title) or "",
        }

        container_title = self._clean_text(getattr(metadata, "container_title", None))
        publisher = self._clean_text(getattr(metadata, "publisher", None))

        if container_title:
            csl_item["container-title"] = container_title
        elif publisher and csl_type == "article-journal":
            csl_item["container-title"] = publisher
        elif publisher:
            csl_item["publisher"] = publisher

        if metadata.authors:
            authors = []
            for a in metadata.authors:
                family = self._clean_text(getattr(a, "family_name", None))
                given = self._clean_text(getattr(a, "given_name", None))
                if family and given:
                    authors.append({"family": family, "given": given})
                elif family:
                    authors.append({"family": family})
            if authors:
                csl_item["author"] = authors

        if getattr(metadata, "publication_year", None):
            csl_item["issued"] = {"date-parts": [[metadata.publication_year]]}

        volume = self._clean_text(getattr(metadata, "volume", None))
        if volume:
            csl_item["volume"] = volume

        issue = self._clean_text(getattr(metadata, "issue", None))
        if issue:
            csl_item["issue"] = issue

        pages = self._clean_text(getattr(metadata, "pages", None))
        if pages:
            csl_item["page"] = pages

        doi = self._clean_text(getattr(metadata, "doi", None))
        if doi:
            csl_item["DOI"] = doi

        return [csl_item]

    def generate_all_citations(self, metadata: CitationMetadata) -> Dict[str, Dict[str, str]]:
        csl_json_data = self._map_to_csl_json(metadata)
        results: Dict[str, Dict[str, str]] = {}
        
        is_preprint = bool(getattr(metadata, "publisher", None) and not getattr(metadata, "container_title", None))

        for style_display_name, style_id in self.STYLES.items():
            style_path = str(self.style_dir / f"{style_id}.csl")
            try:
                style = CitationStylesStyle(style_path, validate=False)
                bib_source = CiteProcJSON(csl_json_data)
                bibliography = CitationStylesBibliography(style, bib_source, formatter.plain)

                citation_item = Citation([CitationItem("item-1")])
                bibliography.register(citation_item)
                
                # 1. Generate In-Text Citation
                in_text_raw = str(bibliography.cite(citation_item, formatter.plain)).strip()
                
                # 2. Generate Full Bibliography
                rendered_entries = bibliography.bibliography()
                raw_rendered = str(rendered_entries[0]).strip() if rendered_entries else ""
                
                clean_rendered = CitationNormalizer.normalize(
                    raw_rendered, 
                    style=style_display_name, 
                    is_preprint=is_preprint
                )
                
                results[style_display_name] = {
                    "in_text": in_text_raw,
                    "bibliography": clean_rendered
                }
            except Exception as e:
                results[style_display_name] = {
                    "in_text": f"[Error: {e}]",
                    "bibliography": f"Formatting error: {e}"
                }

        return results
