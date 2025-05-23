from dataclasses import dataclass
from enum import Enum
from typing import Optional
from datetime import datetime

from pydantic import BaseModel, HttpUrl

# Moved from scraper.configs.models
class Status(Enum):
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class ResponseJSON:
    status: Status
    message: str


@dataclass
class ResponseContent:
    content: str
    title: str

# Pydantic Schemas for API responses
class SiteResponse(BaseModel):
    id: int
    title: Optional[str] = None
    published_date: datetime
    keyword: str
    content: Optional[str] = None
    masked_url: str
    url: str
    is_extracted: bool
    has_rc_analysis: bool
    rc_analysis: Optional[str] = None
    has_sentiment_analysis: bool
    sentiment_analysis: Optional[str] = None
    has_prominent_analysis: bool
    prominent_analysis: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Pydantic Schemas for API request validation
class URLRequest(BaseModel):
    url: HttpUrl

class NewsRequest(BaseModel):
    keyword: str
    use_rca: bool
