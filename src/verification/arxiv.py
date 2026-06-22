import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import re
from typing import Optional
from src.schemas import CitationMetadata, Author

ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
NS = {"atom": ATOM_NS, "arxiv": ARXIV_NS}

def safe_text(element: Optional[ET.Element], path: str, default: Optional[str] = None) -> Optional[str]:
    if element is None:
        return default
    value = element.findtext(path, default=None, namespaces=NS)
    if value is None:
        return default
    value = value.strip()
    return value if value else default

def fetch_arxiv_feed(arxiv_id: str) -> bytes:
    base_url = "https://export.arxiv.org/api/query"
    query = urllib.parse.urlencode({"id_list": arxiv_id})
    url = f"{base_url}?{query}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 Python urllib",
            "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    with urllib.request.urlopen(req, timeout=10) as response:
        return response.read()

def fetch_metadata_from_arxiv(arxiv_id: str) -> CitationMetadata:
    xml_bytes = fetch_arxiv_feed(arxiv_id)
    root = ET.fromstring(xml_bytes)
    entry = root.find("atom:entry", NS)

    if entry is None:
        raise ValueError(f"No entry returned by arXiv API for ID: {arxiv_id}")

    authors_list = []
    for author in entry.findall("atom:author", NS):
        name = safe_text(author, "atom:name")
        if name:
            parts = name.split()
            family = parts[-1] if parts else "Unknown"
            given = " ".join(parts[:-1]) if len(parts) > 1 else None
            authors_list.append(Author(family_name=family, given_name=given))

    published_str = safe_text(entry, "atom:published")
    pub_year = int(published_str[:4]) if published_str and len(published_str) >= 4 else None

    doi_from_feed = safe_text(entry, "arxiv:doi")
    
    doi_fallback = None
    base_id_match = re.match(r"(?P<base>\d{4}\.\d{4,5})", arxiv_id)
    if base_id_match:
        doi_fallback = f"10.48550/arXiv.{base_id_match.group('base')}"

    final_doi = doi_from_feed or doi_fallback

    return CitationMetadata(
        title=safe_text(entry, "atom:title", "Unknown Title"),
        authors=authors_list,
        publication_year=pub_year,
        publisher="arXiv",
        container_title=f"arXiv preprint arXiv:{arxiv_id}",
        volume=None,
        issue=None,
        pages=None,
        doi=final_doi
    )
