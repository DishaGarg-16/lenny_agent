import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class SessionModel(Base):
    """Represents a conversation thread."""
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    title: Mapped[str] = mapped_column(String(255), default="New Conversation")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    messages: Mapped[List["MessageModel"]] = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    artifacts: Mapped[List["ArtifactModel"]] = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan")

class MessageModel(Base):
    """Represents a single chat turn (user or assistant)."""
    __tablename__ = "messages"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    model_used: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="messages")
    citations: Mapped[List["CitationModel"]] = relationship("CitationModel", back_populates="message", cascade="all, delete-orphan")
    artifacts: Mapped[List["ArtifactModel"]] = relationship("ArtifactModel", back_populates="message", cascade="all, delete-orphan")

class CitationModel(Base):
    """Represents a source citation attached to an assistant message."""
    __tablename__ = "citations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    message_id: Mapped[str] = mapped_column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), index=True)
    episode_title: Mapped[str] = mapped_column(String(255))
    guest: Mapped[str] = mapped_column(String(128))
    timestamp_str: Mapped[str] = mapped_column(String(32))
    snippet: Mapped[str] = mapped_column(Text)
    similarity_score: Mapped[float] = mapped_column(Float, default=0.0)
    source_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    message: Mapped["MessageModel"] = relationship("MessageModel", back_populates="citations")

class ArtifactModel(Base):
    """Represents a generated Markdown essay or sandboxed HTML/CSS artifact."""
    __tablename__ = "artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    artifact_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    session: Mapped["SessionModel"] = relationship("SessionModel", back_populates="artifacts")
    message: Mapped[Optional["MessageModel"]] = relationship("MessageModel", back_populates="artifacts")
