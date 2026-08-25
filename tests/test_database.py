import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.db.models import Base
from src.db.repository import ChatRepository


@pytest_asyncio.fixture
async def test_db_session():
    """Provides an isolated in-memory SQLite database session for each test."""
    test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_maker() as session:
        yield session

    await test_engine.dispose()


@pytest.mark.asyncio
async def test_session_lifecycle(test_db_session: AsyncSession):
    repo = ChatRepository(test_db_session)

    # 1. Create session
    session = await repo.create_session("PLG Strategy Discussion")
    assert session.id is not None
    assert session.title == "PLG Strategy Discussion"

    # 2. List sessions
    sessions = await repo.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].id == session.id

    # 3. Retrieve session
    fetched = await repo.get_session(session.id)
    assert fetched is not None
    assert fetched.title == "PLG Strategy Discussion"

    # 4. Delete session
    deleted = await repo.delete_session(session.id)
    assert deleted is True
    assert await repo.get_session(session.id) is None


@pytest.mark.asyncio
async def test_messages_and_citations(test_db_session: AsyncSession):
    repo = ChatRepository(test_db_session)
    session = await repo.create_session("Founder PM Chat")

    # Add user message
    user_msg = await repo.add_message(
        session_id=session.id,
        role="user",
        content="How does Brian Chesky run product reviews?"
    )
    assert user_msg.id is not None
    assert user_msg.role == "user"

    # Add assistant message with citations
    citations_data = [{
        "episode_title": "Redesigning Airbnb",
        "guest": "Brian Chesky",
        "timestamp_str": "00:14:22",
        "snippet": "I review every major product change weekly...",
        "similarity_score": 0.88
    }]
    asst_msg = await repo.add_message(
        session_id=session.id,
        role="assistant",
        content="Brian Chesky runs reviews weekly with interactive Figma prototypes.",
        model_used="ollama/llama3.2",
        citations=citations_data
    )
    assert asst_msg.role == "assistant"
    assert len(asst_msg.citations) == 1
    assert asst_msg.citations[0].guest == "Brian Chesky"

    # Reload session and verify complete history
    loaded = await repo.get_session(session.id)
    assert len(loaded.messages) == 2
    assert loaded.messages[1].citations[0].guest == "Brian Chesky"


@pytest.mark.asyncio
async def test_artifact_persistence(test_db_session: AsyncSession):
    repo = ChatRepository(test_db_session)
    session = await repo.create_session("Artifact Test")

    artifact = await repo.save_artifact(
        session_id=session.id,
        title="Ship 30 for 30 Essay",
        artifact_type="markdown",
        content="# The 3 Non-Obvious Laws of PLG\n\nMost founders get PLG wrong..."
    )
    assert artifact.id is not None
    assert artifact.artifact_type == "markdown"

    fetched = await repo.get_artifact(artifact.id)
    assert fetched is not None
    assert fetched.title == "Ship 30 for 30 Essay"
