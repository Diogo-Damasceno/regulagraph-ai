import enum
import uuid
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ProcessingStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class Norm(Base):
    __tablename__ = "norms"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(300))
    agency: Mapped[str] = mapped_column(String(80), index=True)
    norm_type: Mapped[str] = mapped_column(String(80), default="Resolução")
    number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_hash: Mapped[str] = mapped_column(String(64), unique=True)
    published_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus), default=ProcessingStatus.pending)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provisions: Mapped[list["Provision"]] = relationship(cascade="all, delete-orphan")


class Provision(Base):
    __tablename__ = "provisions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    norm_id: Mapped[str] = mapped_column(ForeignKey("norms.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    text: Mapped[str] = mapped_column(Text)
    page: Mapped[int] = mapped_column(Integer, default=1)
    position: Mapped[int] = mapped_column(Integer, default=0)
    extraction: Mapped[dict] = mapped_column(JSON, default=dict)


class Relation(Base):
    __tablename__ = "relations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_norm_id: Mapped[str] = mapped_column(ForeignKey("norms.id"), index=True)
    target_reference: Mapped[str] = mapped_column(String(300))
    relation_type: Mapped[str] = mapped_column(String(50))
    evidence: Mapped[str] = mapped_column(Text)
    page: Mapped[int] = mapped_column(Integer)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)


class Review(Base):
    __tablename__ = "reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50))
    entity_id: Mapped[str] = mapped_column(String(36), index=True)
    verdict: Mapped[str] = mapped_column(String(40))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
