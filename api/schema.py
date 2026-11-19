from typing import Optional, List
from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Search query string")
    domain: Optional[str] = Field(
        None,
        description="Optional domain filter (e.g. backend, dsa, ai, sql, other)"
    )
    limit: int = Field(
        5,
        ge=1,
        le=10,
        description="Number of results to return (default 5)"
    )


class SearchResultItem(BaseModel):
    id: str = Field(..., description="Stable chunk identifier for React keys")
    rank: int = Field(..., description="1-indexed display order")
    title: str = Field(..., description="Original video title")
    video_id: str = Field(..., description="YouTube video ID for embed")
    video_url: str = Field(..., description="Original YouTube watch URL")
    start: float = Field(..., description="Segment start time in seconds")
    end: float = Field(..., description="Segment end time in seconds")
    start_formatted: str = Field(..., description="Human-readable start timestamp (e.g. 04:00)")
    end_formatted: str = Field(..., description="Human-readable end timestamp (e.g. 05:15)")
    domains: List[str] = Field(default_factory=list, description="Associated domain tags")
    text: str = Field(..., description="Retrieved transcript excerpt")


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class HealthResponse(BaseModel):
    status: str
    collection: str
