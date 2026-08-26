import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.database import get_db
from src.db.repository import ChatRepository
from src.knowledge.retriever import TranscriptRetriever
from src.agent.llm_client import get_llm_client, OllamaLLMClient
from src.agent.core import LennyGrowthAgent
from src.agent.skills.ship30 import Ship30Skill
from src.security.sanitizer import sanitize_html_artifact, sanitize_user_prompt
from .schemas import (
    HealthResponse, ModelsResponse, ModelInfo, SessionCreateRequest,
    SessionResponse, SessionDetailResponse, MessageResponse,
    CitationResponse, ArtifactResponse, ChatRequest, ChatResponse, Ship30Request
)

router = APIRouter()
_retriever: Optional[TranscriptRetriever] = None

def get_retriever() -> TranscriptRetriever:
    global _retriever
    if _retriever is None:
        db_dir = os.getenv("VECTOR_DB_DIR", "./data/vector_db")
        threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.25"))
        _retriever = TranscriptRetriever(persist_directory=db_dir, similarity_threshold=threshold)
    return _retriever

@router.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db), retriever: TranscriptRetriever = Depends(get_retriever)):
    """Diagnostics endpoint verifying database, vector store, and LLM status."""
    components = {}
    try:
        repo = ChatRepository(db)
        await repo.list_sessions(limit=1)
        components["database"] = "connected (PostgreSQL/SQLite)"
    except Exception as e:
        components["database"] = f"error: {str(e)}"
    try:
        count = retriever.count()
        components["vector_store"] = f"ready ({count} chunks indexed)"
    except Exception as e:
        components["vector_store"] = f"error: {str(e)}"
    ollama = OllamaLLMClient()
    is_ollama_up = await ollama.is_available()
    components["ollama_local"] = f"available (model: {ollama.model})" if is_ollama_up else "offline (start with `ollama serve`)"
    has_anthropic, has_openai = bool(os.getenv("ANTHROPIC_API_KEY")), bool(os.getenv("OPENAI_API_KEY"))
    components["cloud_llm"] = "configured (Anthropic)" if has_anthropic else ("configured (OpenAI)" if has_openai else "none (using local Ollama)")
    return HealthResponse(
        status="healthy" if components.get("database", "").startswith("connected") else "degraded",
        timestamp=datetime.now(timezone.utc).isoformat(),
        components=components
    )

@router.get("/api/models", response_model=ModelsResponse)
async def list_models():
    """Lists available local and cloud models."""
    default_provider = os.getenv("DEFAULT_LLM_PROVIDER", "ollama")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
    ollama = OllamaLLMClient()
    ollama_ready = await ollama.is_available()
    models = [
        ModelInfo(id=f"ollama/{ollama_model}", name="Llama 3.2 (Local Ollama)", provider="ollama", is_local=True, is_available=ollama_ready),
        ModelInfo(id="anthropic/claude-3-5-sonnet-20241022", name="Claude 3.5 Sonnet (Cloud)", provider="anthropic", is_local=False, is_available=bool(os.getenv("ANTHROPIC_API_KEY"))),
        ModelInfo(id="openai/gpt-4o", name="GPT-4o (Cloud)", provider="openai", is_local=False, is_available=bool(os.getenv("OPENAI_API_KEY")))
    ]
    return ModelsResponse(
        active_model=f"ollama/{ollama_model}" if default_provider == "ollama" else "anthropic/claude-3-5-sonnet-20241022",
        models=models
    )

@router.post("/api/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(req: SessionCreateRequest, db: AsyncSession = Depends(get_db)):
    """Creates a new conversation session."""
    repo = ChatRepository(db)
    session = await repo.create_session(title=req.title or "New Conversation")
    return SessionResponse(id=session.id, title=session.title, created_at=session.created_at, updated_at=session.updated_at, message_count=0)

@router.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(limit: int = 50, db: AsyncSession = Depends(get_db)):
    """Lists all recent conversation sessions."""
    repo = ChatRepository(db)
    sessions = await repo.list_sessions(limit=limit)
    return [
        SessionResponse(
            id=s.id, title=s.title, created_at=s.created_at, updated_at=s.updated_at,
            message_count=len(s.messages) if hasattr(s, "messages") and s.messages else 0
        ) for s in sessions
    ]

@router.get("/api/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full conversation history and generated artifacts for a session."""
    repo = ChatRepository(db)
    session = await repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = [
        MessageResponse(
            id=m.id, session_id=m.session_id, role=m.role, content=m.content, model_used=m.model_used, created_at=m.created_at,
            citations=[CitationResponse(episode_title=c.episode_title, guest=c.guest, timestamp_str=c.timestamp_str, snippet=c.snippet, similarity_score=c.similarity_score, source_url=c.source_url) for c in m.citations]
        ) for m in session.messages
    ]
    artifacts = [
        ArtifactResponse(id=a.id, session_id=a.session_id, title=a.title, artifact_type=a.artifact_type, content=a.content, version=a.version, created_at=a.created_at)
        for a in session.artifacts
    ]
    return SessionDetailResponse(id=session.id, title=session.title, created_at=session.created_at, updated_at=session.updated_at, messages=messages, artifacts=artifacts)

@router.delete("/api/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """Deletes a conversation session."""
    repo = ChatRepository(db)
    deleted = await repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return None

@router.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest, db: AsyncSession = Depends(get_db), retriever: TranscriptRetriever = Depends(get_retriever)):
    """Grounded Conversational RAG Endpoint with security sanitization and persistence."""
    clean_message = sanitize_user_prompt(req.message)
    repo = ChatRepository(db)
    session = await repo.get_session(req.session_id) if req.session_id else None
    if not session:
        session = await repo.create_session(title=clean_message[:40] + ("..." if len(clean_message) > 40 else ""))
    elif session.title == "New Conversation":
        session.title = clean_message[:40] + ("..." if len(clean_message) > 40 else "")
        await db.commit()
    session_id = session.id
    await repo.add_message(session_id=session_id, role="user", content=clean_message)
    chat_history = [{"role": m.role, "content": m.content} for m in session.messages[-6:]] if session.messages else []
    llm_client = get_llm_client(req.model_override)
    agent = LennyGrowthAgent(retriever=retriever, llm_client=llm_client)
    agent_resp = await agent.chat(user_message=clean_message, chat_history=chat_history)
    citations_payload = [c.model_dump() for c in agent_resp.citations]
    asst_msg = await repo.add_message(session_id=session_id, role="assistant", content=agent_resp.answer, model_used=agent_resp.model_used, citations=citations_payload)
    artifact_res = None
    if agent_resp.artifact_type and agent_resp.artifact_content:
        clean_content = sanitize_html_artifact(agent_resp.artifact_content) if agent_resp.artifact_type == "html" else agent_resp.artifact_content
        saved_art = await repo.save_artifact(
            session_id=session_id, title=agent_resp.artifact_title or "Generated Artifact",
            artifact_type=agent_resp.artifact_type, content=clean_content, message_id=asst_msg.id
        )
        artifact_res = ArtifactResponse(id=saved_art.id, session_id=saved_art.session_id, title=saved_art.title, artifact_type=saved_art.artifact_type, content=saved_art.content, version=saved_art.version, created_at=saved_art.created_at)
    return ChatResponse(
        session_id=session_id, message_id=asst_msg.id, role="assistant", content=agent_resp.answer, model_used=agent_resp.model_used,
        citations=[CitationResponse(**c.model_dump()) for c in agent_resp.citations], artifact=artifact_res, is_grounded=agent_resp.is_grounded
    )

@router.post("/api/skills/ship30", response_model=ChatResponse)
async def ship30_endpoint(req: Ship30Request, db: AsyncSession = Depends(get_db), retriever: TranscriptRetriever = Depends(get_retriever)):
    """Dedicated Ship 30 for 30 essay generation endpoint."""
    clean_topic = sanitize_user_prompt(req.topic)
    repo = ChatRepository(db)
    session_title = f"Ship 30: {clean_topic[:35]}"
    session = await repo.get_session(req.session_id) if req.session_id else None
    if not session:
        session = await repo.create_session(title=session_title)
    elif session.title == "New Conversation":
        session.title = session_title
        await db.commit()
    session_id = session.id
    user_prompt = f"Write a Ship 30 for 30 essay on: {clean_topic}" + (f" (Focus: {req.guest_filter})" if req.guest_filter else "")
    await repo.add_message(session_id=session_id, role="user", content=user_prompt)
    llm_client = get_llm_client(req.model_override)
    skill = Ship30Skill(retriever=retriever, llm_client=llm_client)
    essay_resp = await skill.generate_essay(topic=clean_topic, guest_filter=req.guest_filter)

    # Do not create empty artifacts on rejected / out-of-scope topics
    if essay_resp.word_count == 0 or len(essay_resp.citations) == 0:
        refusal_text = "This topic is not covered in Lenny's Podcast transcripts."
        asst_msg = await repo.add_message(session_id=session_id, role="assistant", content=refusal_text, model_used=llm_client.model_name)
        return ChatResponse(
            session_id=session_id, message_id=asst_msg.id, role="assistant", content=refusal_text, model_used=llm_client.model_name,
            citations=[], artifact=None, is_grounded=False
        )

    summary_text = f"Here is your **Ship 30 for 30** essay on **{clean_topic}** ({essay_resp.word_count} words):\n\n> *\"{essay_resp.hook}\"*\n\nThe full essay has been loaded into the **Artifact Viewer** on the right."
    citations_payload = [c.model_dump() for c in essay_resp.citations]
    asst_msg = await repo.add_message(session_id=session_id, role="assistant", content=summary_text, model_used=llm_client.model_name, citations=citations_payload)
    saved_art = await repo.save_artifact(
        session_id=session_id, title=essay_resp.title, artifact_type="markdown", content=essay_resp.markdown_content, message_id=asst_msg.id
    )
    artifact_res = ArtifactResponse(id=saved_art.id, session_id=saved_art.session_id, title=saved_art.title, artifact_type=saved_art.artifact_type, content=saved_art.content, version=saved_art.version, created_at=saved_art.created_at)
    return ChatResponse(
        session_id=session_id, message_id=asst_msg.id, role="assistant", content=summary_text, model_used=llm_client.model_name,
        citations=[CitationResponse(**c.model_dump()) for c in essay_resp.citations], artifact=artifact_res, is_grounded=True
    )

@router.get("/api/artifacts/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves a persisted artifact by ID."""
    repo = ChatRepository(db)
    artifact = await repo.get_artifact(artifact_id)
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return ArtifactResponse(id=artifact.id, session_id=artifact.session_id, title=artifact.title, artifact_type=artifact.artifact_type, content=artifact.content, version=artifact.version, created_at=artifact.created_at)
