from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import re

class Author(BaseModel):
    family_name: str
    given_name: Optional[str] = None

class CitationMetadata(BaseModel):
    title: str
    authors: List[Author] = Field(default_factory=list)
    publication_year: Optional[int] = None
    publisher: Optional[str] = None
    container_title: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    pages: Optional[str] = None
    doi: Optional[str] = None

    @field_validator('doi', mode='before')
    @classmethod
    def clean_doi(cls, value):
        if value:
            match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', str(value), re.IGNORECASE)
            if match:
                return match.group(1)
        return value
