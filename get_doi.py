import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


ATOM_NS = "http://www.w3.org/2005/Atom"
ARXIV_NS = "http://arxiv.org/schemas/atom"
OPENSEARCH_NS = "http://a9.com/-/spec/opensearch/1.1/"

NS = {
    "atom": ATOM_NS,
    "arxiv": ARXIV_NS,
    "opensearch": OPENSEARCH_NS,
}


def normalize_arxiv_id(raw_input_string):
    """
    Extract and normalize an arXiv identifier.

    Returns:
        tuple[str, str, str | None]:
            full_id:  identifier with version if present
            base_id:  identifier without version
            version:  version string like 'v6' or None
    """
    text = str(raw_input_string).strip()

    patterns = [
        # New-style IDs: 1706.03762 or 1706.03762v6
        r"(?:arXiv:)?(?P<base>\d{4}\.\d{4,5})(?P<version>v\d+)?",
        # Old-style IDs: hep-th/9901001 or hep-th/9901001v3
        r"(?:arXiv:)?(?P<base>[A-Za-z\-]+(?:\.[A-Z]{2})?/\d{7})(?P<version>v\d+)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            base_id = match.group("base")
            version = match.group("version")
            full_id = base_id + (version or "")
            return full_id, base_id, version

    return None, None, None


def safe_text(element, path, default=None):
    if element is None:
        return default
    value = element.findtext(path, default=None, namespaces=NS)
    if value is None:
        return default
    value = value.strip()
    return value if value else default


def fetch_arxiv_feed(full_id):
    """
    Query the arXiv API for one specific id/version.
    """
    base_url = "https://export.arxiv.org/api/query"
    query = urllib.parse.urlencode({"id_list": full_id})
    url = f"{base_url}?{query}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Python urllib",
            "Accept": "application/atom+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )

    with urllib.request.urlopen(req, timeout=20) as response:
        return response.read()


def parse_arxiv_xml(xml_bytes, base_id, full_id):
    root = ET.fromstring(xml_bytes)
    entry = root.find("atom:entry", NS)

    if entry is None:
        feed_title = safe_text(root, "atom:title", "ArXiv Query")
        total_results = safe_text(root, "opensearch:totalResults", None)
        return {
            "error": "No entry returned by arXiv API",
            "feed_title": feed_title,
            "total_results": total_results,
            "arxiv_id": full_id,
        }

    entry_title = safe_text(entry, "atom:title")
    if entry_title and entry_title.lower() == "error":
        return {
            "error": safe_text(entry, "atom:summary", "arXiv returned an error"),
            "arxiv_id": full_id,
            "api_error_id": safe_text(entry, "atom:id"),
        }

    authors = []
    for author in entry.findall("atom:author", NS):
        name = safe_text(author, "atom:name")
        if name:
            authors.append(name)

    categories = []
    primary_category = None
    for category in entry.findall("atom:category", NS):
        term = category.attrib.get("term")
        if term:
            categories.append(term)
            if primary_category is None:
                primary_category = term

    journal_ref = safe_text(entry, "arxiv:journal_ref")
    doi_from_feed = safe_text(entry, "arxiv:doi")
    comment = safe_text(entry, "arxiv:comment")

    abs_url = safe_text(entry, "atom:id") or f"https://arxiv.org/abs/{full_id}"
    pdf_url = None

    for link in entry.findall("atom:link", NS):
        href = link.attrib.get("href")
        rel = link.attrib.get("rel")
        title = link.attrib.get("title")
        typ = link.attrib.get("type")

        if href and (
            typ == "application/pdf"
            or title == "pdf"
            or (rel == "related" and href.endswith(".pdf"))
        ):
            pdf_url = href
            break

    if pdf_url is None:
        pdf_url = f"https://arxiv.org/pdf/{base_id}.pdf"

    # arXiv's DOI prefix is 10.48550. For DOI fallback, use the canonical ID
    # without a version, matching the behavior described by arXiv.
    doi_fallback = None
    if re.fullmatch(r"\d{4}\.\d{4,5}", base_id):
        doi_fallback = f"10.48550/arXiv.{base_id}"

    output = {
        "arxiv_id": full_id,
        "canonical_arxiv_id": base_id,
        "version": full_id[len(base_id):] if len(full_id) > len(base_id) else None,
        "title": entry.findtext("atom:title", default="", namespaces=NS).strip() or None,
        "authors": authors,
        "summary": safe_text(entry, "atom:summary"),
        "published": safe_text(entry, "atom:published"),
        "updated": safe_text(entry, "atom:updated"),
        "categories": categories,
        "primary_category": primary_category,
        "comment": comment,
        "journal_ref": journal_ref,
        "doi": doi_from_feed or doi_fallback,
        "abs_url": abs_url,
        "pdf_url": pdf_url,
    }

    return output


def get_full_metadata(raw_input_string):
    full_id, base_id, version = normalize_arxiv_id(raw_input_string)

    if not full_id:
        return json.dumps(
            {"error": "No valid arXiv ID found"},
            indent=4,
            ensure_ascii=False,
        )

    try:
        xml_bytes = fetch_arxiv_feed(full_id)
        data = parse_arxiv_xml(xml_bytes, base_id, full_id)
        return json.dumps(data, indent=4, ensure_ascii=False)

    except urllib.error.HTTPError as e:
        return json.dumps(
            {
                "error": "HTTP error while contacting arXiv",
                "arxiv_id": full_id,
                "status_code": e.code,
                "details": str(e),
            },
            indent=4,
            ensure_ascii=False,
        )

    except urllib.error.URLError as e:
        return json.dumps(
            {
                "error": "Connection failed",
                "arxiv_id": full_id,
                "tip": "Check network/DNS access to export.arxiv.org, or run offline mode with cached data.",
                "details": str(e),
            },
            indent=4,
            ensure_ascii=False,
        )

    except ET.ParseError as e:
        return json.dumps(
            {
                "error": "Invalid XML received from arXiv",
                "arxiv_id": full_id,
                "details": str(e),
            },
            indent=4,
            ensure_ascii=False,
        )

    except Exception as e:
        return json.dumps(
            {
                "error": "Unexpected failure",
                "arxiv_id": full_id,
                "details": str(e),
            },
            indent=4,
            ensure_ascii=False,
        )


if __name__ == "__main__":
    arxiv_string = sys.argv[1] if len(sys.argv) > 1 else "1706.03762"
    print(get_full_metadata(arxiv_string))
