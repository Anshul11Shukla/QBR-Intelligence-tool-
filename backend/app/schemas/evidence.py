
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


CommitmentStatus = Literal[
    "open", "in_progress", "completed", "blocked"
]


class DocumentResponse(BaseModel):
    id: int
    case_id: int
    filename: str
    document_type: str
    chunk_count: int
    uploaded_at: datetime


class EvidenceHit(BaseModel):
    chunk_id: int
    document_id: int
    filename: str
    source_location: str
    excerpt: str
    citation: str
    relevance_score: float


class SearchResponse(BaseModel):
    case_id: int
    query: str
    results: list[EvidenceHit]
    retrieval_method: str = "SQLite FTS5 BM25"


class CommitmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=300)
    owner: str = Field(min_length=1, max_length=150)
    due_date: date | None = None
    status: CommitmentStatus = "open"
    source_document_id: int | None = None
    source_location: str | None = None

    @field_validator("title", "owner")
    @classmethod
    def strip_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be blank")
        return value


class CommitmentResponse(CommitmentCreate):
    id: int
    case_id: int
    created_at: datetime
