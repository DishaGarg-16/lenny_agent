from typing import List, Optional
from pydantic import BaseModel, Field


class TranscriptMetadata(BaseModel):
    """Metadata extracted from the frontmatter header of a transcript file."""
    episode_title: str = Field(..., description="Full title of the podcast episode")
    guest: str = Field(..., description="Name of the featured guest")
    date: Optional[str] = Field(None, description="Date the episode was published")
    audio_url: Optional[str] = Field(None, description="Direct URL to episode or show notes")
    topics: List[str] = Field(default_factory=list, description="Categorical topic tags")


class TranscriptChunk(BaseModel):
    """Represents a chunked segment of dialogue with timestamp & speaker metadata."""
    chunk_id: str = Field(..., description="Unique chunk identifier, e.g. guest_timestamp_index")
    episode_title: str
    guest: str
    timestamp_str: str = Field(..., description="Timestamp in format [HH:MM:SS] or [MM:SS]")
    speaker: str = Field(..., description="Speaker name (e.g. Lenny Rachitsky, Brian Chesky)")
    text: str = Field(..., description="Text content of this dialogue chunk")
    topics: List[str] = Field(default_factory=list)


class Citation(BaseModel):
    """Verifiable source citation for an answer."""
    episode_title: str
    guest: str
    timestamp_str: str
    snippet: str
    similarity_score: float = Field(default=0.0, description="Cosine similarity score (0.0 - 1.0)")
    source_url: Optional[str] = None


class RetrievalResult(BaseModel):
    """Result returned by the vector search retriever."""
    chunks: List[TranscriptChunk] = Field(default_factory=list)
    citations: List[Citation] = Field(default_factory=list)
    is_grounded: bool = Field(..., description="True if top retrieval score exceeds similarity threshold")
    top_score: float = Field(default=0.0)
