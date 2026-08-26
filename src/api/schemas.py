from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from src.knowledge.schemas import Citation

class HealthResponse(BaseModel):
    """System health check status response."""
    status: str = Field(..., examples=["healthy"])
    timestamp: str
    components: Dict[str, str] = Field(..., description="Status of DB, Vector Store, and Ollama")

class ModelInfo(BaseModel):
    """Metadata for an available LLM engine."""
    id: str = Field(..., examples=["ollama/llama3.2"])
    name: str = Field(..., examples=["Llama 3.2 (Local)"])
    provider: str = Field(..., examples=["ollama"])
    is_local: bool = True
    is_available: bool = True

class ModelsResponse(BaseModel):
    """List of all available local and cloud models."""
    active_model: str
    models: List[ModelInfo]

class SessionCreateRequest(BaseModel):
    """Payload to initialize a new conversation session."""
    title: Optional[str] = Field("New Conversation", max_length=255)

class SessionResponse(BaseModel):
    """Summary representation of a chat session."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0

class CitationResponse(BaseModel):
    """Source attribution citation."""
    episode_title: str
    guest: str
    timestamp_str: str
    snippet: str
    similarity_score: float = 0.0
    source_url: Optional[str] = None

class ArtifactResponse(BaseModel):
    """Generated Markdown or HTML artifact."""
    id: str
    session_id: str
    title: str
    artifact_type: str
    content: str
    version: int = 1
    created_at: datetime

class MessageResponse(BaseModel):
    """Single message in a conversation thread."""
    id: str
    session_id: str
    role: str
    content: str
    model_used: Optional[str] = None
    created_at: datetime
    citations: List[CitationResponse] = Field(default_factory=list)

class SessionDetailResponse(BaseModel):
    """Full session detail including message history and artifacts."""
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = Field(default_factory=list)
    artifacts: List[ArtifactResponse] = Field(default_factory=list)

class ChatRequest(BaseModel):
    """User conversational query request."""
    session_id: Optional[str] = Field(None, description="Optional existing session ID")
    message: str = Field(..., min_length=1, max_length=4000, description="User question or prompt")
    model_override: Optional[str] = Field(None, description="Optional model to route to")
    skill: Optional[str] = Field("default", description="Active skill: 'default' | 'ship30'")

class ChatResponse(BaseModel):
    """Grounded assistant response with citations and artifacts."""
    session_id: str
    message_id: str
    role: str = "assistant"
    content: str
    model_used: str
    citations: List[CitationResponse] = Field(default_factory=list)
    artifact: Optional[ArtifactResponse] = None
    is_grounded: bool = True

class Ship30Request(BaseModel):
    """Request to generate a Ship 30 for 30 digital essay."""
    session_id: Optional[str] = None
    topic: str = Field(..., min_length=3, max_length=500, description="Essay topic or thesis")
    guest_filter: Optional[str] = Field(None, description="Optional guest to emphasize")
    model_override: Optional[str] = None
