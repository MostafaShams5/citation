import httpx
from typing import Optional
from src.schemas import CitationMetadata, Author

def fetch_from_crossref(doi: str) -> CitationMetadata:
    url = f"https://api.crossref.org/works/{doi}"
    
    with httpx.Client() as client:
        response = client.get(url, timeout=5.0)
        
        if response.status_code != 200:
            raise Exception(f"CrossRef lookup failed for {doi} with status {response.status_code}")
            
        data = response.json().get('message', {})
        
        authors_list = []
        for author_data in data.get('author', []):
            authors_list.append(Author(
                family_name=author_data.get('family', 'Unknown'),
                given_name=author_data.get('given')
            ))
            
        pub_year = None
        published_data = data.get('published-print') or data.get('published-online') or data.get('issued')
        if published_data and 'date-parts' in published_data:
            pub_year = published_data['date-parts'][0][0]
            
        # Safely extract container-title (The actual Journal Name, e.g., "Nature")
        container_title = None
        if data.get('container-title') and len(data['container-title']) > 0:
            container_title = data['container-title'][0]
            
        return CitationMetadata(
            title=data.get('title', [''])[0],
            authors=authors_list,
            publication_year=pub_year,
            publisher=data.get('publisher'),
            container_title=container_title,
            volume=data.get('volume'),
            issue=data.get('issue'),
            pages=data.get('page'),
            doi=doi
        )
