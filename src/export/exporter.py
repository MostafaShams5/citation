import logging
from typing import List, Dict
from src.schemas import CitationMetadata

logger = logging.getLogger(__name__)

class CitationExporter:
    """
    Handles the conversion of CitationMetadata into standard academic export formats.
    Fulfills PRD Requirement 4.4: Export Options (RIS, BibTeX, Markdown).
    """

    @staticmethod
    def generate_bibtex_id(metadata: CitationMetadata) -> str:
        author_key = "Unknown"
        if metadata.authors and len(metadata.authors) > 0:
            author_key = metadata.authors[0].family_name.replace(" ", "")
            
        year_key = str(metadata.publication_year) if metadata.publication_year else "n.d."
        return f"{author_key}{year_key}"

    @classmethod
    def to_bibtex(cls, metadata: CitationMetadata) -> str:
        citation_id = cls.generate_bibtex_id(metadata)
        entry_type = "article" if metadata.container_title else "misc"
        
        lines = [f"@{entry_type}{{{citation_id},"]
        
        if metadata.title:
            lines.append(f"  title = {{{metadata.title}}},")
            
        if metadata.authors:
            author_strings = []
            for author in metadata.authors:
                if author.given_name:
                    author_strings.append(f"{author.family_name}, {author.given_name}")
                else:
                    author_strings.append(author.family_name)
            lines.append(f"  author = {{{' and '.join(author_strings)}}},")
            
        if metadata.container_title:
            lines.append(f"  journal = {{{metadata.container_title}}},")
            
        if metadata.publication_year:
            lines.append(f"  year = {{{metadata.publication_year}}},")
            
        if metadata.publisher:
            lines.append(f"  publisher = {{{metadata.publisher}}},")
            
        if metadata.volume:
            lines.append(f"  volume = {{{metadata.volume}}},")
            
        if metadata.issue:
            lines.append(f"  number = {{{metadata.issue}}},")
            
        if metadata.pages:
            lines.append(f"  pages = {{{metadata.pages}}},")
            
        if metadata.doi:
            lines.append(f"  doi = {{{metadata.doi}}},")
            
        if len(lines) > 1:
            lines[-1] = lines[-1].rstrip(',')
            
        lines.append("}")
        return "\n".join(lines)

    @classmethod
    def to_ris(cls, metadata: CitationMetadata) -> str:
        lines = []
        if metadata.container_title:
            lines.append("TY  - JOUR")
        elif metadata.publisher:
            lines.append("TY  - BOOK")
        else:
            lines.append("TY  - GEN")
            
        if metadata.title:
            lines.append(f"TI  - {metadata.title}")
            
        if metadata.authors:
            for author in metadata.authors:
                if author.given_name:
                    lines.append(f"AU  - {author.family_name}, {author.given_name}")
                else:
                    lines.append(f"AU  - {author.family_name}")
                    
        if metadata.container_title:
            lines.append(f"T2  - {metadata.container_title}")
            
        if metadata.publication_year:
            lines.append(f"PY  - {metadata.publication_year}")
            
        if metadata.publisher:
            lines.append(f"PB  - {metadata.publisher}")
            
        if metadata.volume:
            lines.append(f"VL  - {metadata.volume}")
            
        if metadata.issue:
            lines.append(f"IS  - {metadata.issue}")
            
        if metadata.pages:
            if "-" in metadata.pages:
                sp, ep = metadata.pages.split("-", 1)
                lines.append(f"SP  - {sp.strip()}")
                lines.append(f"EP  - {ep.strip()}")
            else:
                lines.append(f"SP  - {metadata.pages}")
                
        if metadata.doi:
            lines.append(f"DO  - {metadata.doi}")
            lines.append(f"UR  - https://doi.org/{metadata.doi}")
            
        lines.append("ER  - ")
        return "\n".join(lines)

    @classmethod
    def to_markdown(cls, formatted_citations: Dict[str, Dict[str, str]]) -> str:
        lines = ["# Generated Citations\n"]
        for style, outputs in formatted_citations.items():
            lines.append(f"### {style}")
            lines.append(f"**In-Text:** {outputs['in_text']}")
            lines.append(f"**Bibliography:** {outputs['bibliography']}\n")
        return "\n".join(lines)

    @classmethod
    def compile_master_bibliography(cls, batch_results: List[Dict]) -> str:
        """
        Fulfills PRD 4.3: Sorts the final compiled bibliography alphabetically 
        by author last name automatically.
        """
        # Sort by the first author's family name
        def get_sort_key(item):
            meta = item["metadata"]
            if meta.authors and len(meta.authors) > 0:
                return meta.authors[0].family_name.lower()
            return meta.title.lower()

        sorted_batch = sorted(batch_results, key=get_sort_key)
        
        # We will compile APA as the default master bibliography format
        lines = ["# Master Compiled Bibliography (Alphabetical)\n"]
        
        for item in sorted_batch:
            bib_entry = item["formatted_citations"]["APA (7th Ed)"]["bibliography"]
            lines.append(f"- {bib_entry}")
            
        return "\n".join(lines)
