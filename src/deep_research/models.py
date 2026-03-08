from pydantic import BaseModel, Field
from typing import List, Optional

class Config(BaseModel):
    gemini_api_key: str
    tavily_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_rpm: int = 15
    max_chars_per_page: int = 8000
    max_concurrent_fetches: int = 5
    fetch_timeout: int = 10

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
    claim: str = Field(description="A specific, factual claim extracted from the page.")
    evidence: str = Field(description="Supporting detail or data point from the page.")
    confidence: str = Field(description="Confidence level: high, medium, or low.")
    url: Optional[str] = Field(None, description="The source URL of the finding.")

class FindingList(BaseModel):
    findings: List[Finding]

class ResearchReport(BaseModel):
    query: str
    summary: str
    sections: List[dict]
    sources: List[str]
