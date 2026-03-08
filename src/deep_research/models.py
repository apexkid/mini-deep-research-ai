from pydantic import BaseModel, Field
from typing import List, Optional

class Config(BaseModel):
    gemini_api_key: str
    tavily_api_key: str
    # Other optional configurations can go here later

class SearchResult(BaseModel):
    url: str
    title: str
    content: str
    score: float

class PageContent(BaseModel):
    url: str
    text: str
    title: Optional[str] = None

class Finding(BaseModel):
    url: str
    claim: str
    evidence: str

class ResearchReport(BaseModel):
    query: str
    summary: str
    sections: List[dict] # Will refine later
    sources: List[str]
