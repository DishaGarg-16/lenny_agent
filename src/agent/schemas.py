from typing import List, Optional
from pydantic import BaseModel, Field
from src.knowledge.schemas import Citation


class AgentResponse(BaseModel):
    """Structured response from the Lenny Growth Assistant Agent."""
    answer: str = Field(..., description="Conversational, grounded response")
    citations: List[Citation] = Field(default_factory=list, description="Verifiable transcript source citations")
    artifact_type: Optional[str] = Field(None, description="Type of generated artifact: 'markdown' | 'html' | None")
    artifact_title: Optional[str] = Field(None, description="Title for the generated artifact")
    artifact_content: Optional[str] = Field(None, description="Raw markdown or HTML artifact code")
    model_used: str = Field(..., description="Identifier of the model that generated this response")
    is_grounded: bool = Field(True, description="Whether the answer is grounded in transcript sources")


class Ship30EssayResponse(BaseModel):
    """Structured output for a Ship 30 for 30 digital essay."""
    title: str = Field(..., description="High-converting, curiosity-inducing essay headline")
    hook: str = Field(..., description="Provocative, single-sentence opening hook")
    word_count: int = Field(..., description="Total word count of the generated essay")
    markdown_content: str = Field(..., description="Full formatted markdown essay (~1,250 words)")
    citations: List[Citation] = Field(default_factory=list, description="Source podcast citations used in the essay")
