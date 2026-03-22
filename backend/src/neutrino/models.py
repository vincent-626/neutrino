from pydantic import BaseModel
from typing import Optional


class SearchRequest(BaseModel):
    query: str
    service: Optional[str] = None
    severity: Optional[str] = None  # e.g. "error", "warn", "info"
    start_ns: int  # nanosecond epoch
    end_ns: int    # nanosecond epoch
    top_k: Optional[int] = None


class LogResult(BaseModel):
    score: float
    timestamp_ns: int
    labels: dict[str, str]
    line: str


class SearchResponse(BaseModel):
    results: list[LogResult]
    total_fetched: int
    truncated: bool = False


class LabelsResponse(BaseModel):
    values: list[str]
