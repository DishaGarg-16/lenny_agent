from typing import List, Optional, Dict, Any
from sqlalchemy import select, delete, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SessionModel, MessageModel, CitationModel, ArtifactModel

class ChatRepository:
    """Async repository for managing sessions, messages, citations, and artifacts."""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(self, title: str = "New Conversation") -> SessionModel:
        """Creates and persists a new chat session."""
        new_session = SessionModel(title=title)
        self.session.add(new_session)
        await self.session.commit()
        session_id = new_session.id
        return await self.get_session(session_id)

    async def get_session(self, session_id: str) -> Optional[SessionModel]:
        """Retrieves a session by ID with its messages, citations, and artifacts pre-loaded."""
        stmt = (
            select(SessionModel).where(SessionModel.id == session_id)
            .options(
                selectinload(SessionModel.messages).selectinload(MessageModel.citations),
                selectinload(SessionModel.artifacts)
            )
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def list_sessions(self, limit: int = 50) -> List[SessionModel]:
        """Lists all chat sessions with messages eager-loaded, ordered by most recently updated."""
        stmt = (
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .order_by(desc(SessionModel.updated_at))
            .limit(limit)
            .execution_options(populate_existing=True)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_session(self, session_id: str) -> bool:
        """Deletes a session and cascades to messages, citations, and artifacts."""
        stmt = delete(SessionModel).where(SessionModel.id == session_id)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0

    async def add_message(
        self, session_id: str, role: str, content: str,
        model_used: Optional[str] = None, citations: Optional[List[Dict[str, Any]]] = None
    ) -> MessageModel:
        """Appends a message (and optional citations) to a session."""
        msg = MessageModel(session_id=session_id, role=role, content=content, model_used=model_used)
        self.session.add(msg)
        await self.session.flush()
        if citations:
            for cit in citations:
                citation_obj = CitationModel(
                    message_id=msg.id, episode_title=cit.get("episode_title", ""), guest=cit.get("guest", ""),
                    timestamp_str=cit.get("timestamp_str", ""), snippet=cit.get("snippet", ""),
                    similarity_score=float(cit.get("similarity_score", 0.0)), source_url=cit.get("source_url")
                )
                self.session.add(citation_obj)
        await self.session.commit()
        stmt = select(MessageModel).where(MessageModel.id == msg.id).options(selectinload(MessageModel.citations))
        res = await self.session.execute(stmt)
        return res.scalars().first()

    async def save_artifact(self, session_id: str, title: str, artifact_type: str, content: str, message_id: Optional[str] = None) -> ArtifactModel:
        """Persists a generated Markdown or HTML artifact."""
        artifact = ArtifactModel(session_id=session_id, message_id=message_id, title=title, artifact_type=artifact_type, content=content)
        self.session.add(artifact)
        await self.session.commit()
        return await self.get_artifact(artifact.id)

    async def get_artifact(self, artifact_id: str) -> Optional[ArtifactModel]:
        """Retrieves an artifact by ID."""
        stmt = select(ArtifactModel).where(ArtifactModel.id == artifact_id).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalars().first()
