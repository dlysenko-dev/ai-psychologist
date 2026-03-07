"""Knowledge document model for RAG"""
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from backend.database import Base, TimestampMixin

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


class KnowledgeDocument(Base, TimestampMixin):
    __tablename__ = "psych_knowledge_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[Optional[str]] = mapped_column(String(500), default=None)
    category: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    # Categories: neurobiology, cognitive_bias, money_scripts, cbt, act, mi, sfbt, ba, assessment, intervention

    embedding = mapped_column(Vector(384), nullable=True) if Vector else None
    extra_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=None)
