import re
from typing import Optional

def extract_doi_deterministic(raw_text: str) -> Optional[str]:
    match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', raw_text, re.IGNORECASE)
    if match:
        return match.group(1).rstrip('.:,;')
    return None

def extract_arxiv_id_deterministic(raw_text: str) -> Optional[str]:
    patterns = [
        r"(?:arXiv:)?(?P<base>\d{4}\.\d{4,5})(?P<version>v\d+)?",
        r"(?:arXiv:)?(?P<base>[A-Za-z\-]+(?:\.[A-Z]{2})?/\d{7})(?P<version>v\d+)?"
    ]
    for pattern in patterns:
        match = re.search(pattern, raw_text)
        if match:
            base_id = match.group("base")
            version = match.group("version")
            return base_id + (version or "")
    return None
