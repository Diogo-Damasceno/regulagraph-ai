from datetime import date
from pydantic import BaseModel, Field


class Evidence(BaseModel):
    document_id: str
    provision: str
    page: int
    quote: str


class Obligation(BaseModel):
    subject: str
    action: str
    deadline: str | None = None
    confidence: float = Field(ge=0, le=1)
    evidence: Evidence


class Change(BaseModel):
    change_type: str
    provision: str
    before: str | None = None
    after: str | None = None
    summary: str
    affected_entities: list[str] = []
    confidence: float = Field(ge=0, le=1)


class NormCreate(BaseModel):
    title: str
    agency: str
    text: str
    norm_type: str = "Resolução"
    number: str | None = None
    source_url: str | None = None
    published_at: date | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class QuestionRequest(BaseModel):
    question: str
    reference_date: date | None = None
    agency: str | None = None


class ReviewCreate(BaseModel):
    entity_type: str
    entity_id: str
    verdict: str
    comment: str | None = None
