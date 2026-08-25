import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from src.db.models import Base
from src.db.database import get_db
from src.api.main import app
from src.api.routes import get_retriever
from src.knowledge.retriever import TranscriptRetriever


@pytest_asyncio.fixture
async def test_client(tmp_path: Path):
    """Provides a test client configured with isolated in-memory DB and temp vector store."""
    test_db_url = "sqlite+aiosqlite:///:memory:"
    engine = create_async_engine(test_db_url, echo=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_maker() as session:
            yield session

    # Setup temp transcript and retriever
    transcripts_path = tmp_path / "transcripts"
    transcripts_path.mkdir(parents=True, exist_ok=True)
    sample_file = transcripts_path / "sample.md"
    sample_file.write_text("""---
episode_title: "Airbnb Growth"
guest: "Brian Chesky"
date: "2023-11-05"
topics: ["founder-led pm"]
---

[00:01:10] Brian Chesky: We combined product marketing with product management.
""", encoding="utf-8")

    test_retriever = TranscriptRetriever(
        persist_directory=str(tmp_path / "api_test_vec"),
        similarity_threshold=0.30
    )
    test_retriever.index_directory(str(transcripts_path))

    def override_get_retriever():
        return test_retriever

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_retriever] = override_get_retriever

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_endpoint(test_client: AsyncClient):
    response = await test_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data["components"]
    assert "vector_store" in data["components"]


@pytest.mark.asyncio
async def test_list_models_endpoint(test_client: AsyncClient):
    response = await test_client.get("/api/models")
    assert response.status_code == 200
    data = response.json()
    assert "models" in data
    assert len(data["models"]) >= 1
    assert data["models"][0]["provider"] == "ollama"


@pytest.mark.asyncio
async def test_session_crud_endpoints(test_client: AsyncClient):
    # 1. Create Session
    create_res = await test_client.post("/api/sessions", json={"title": "Test Chat"})
    assert create_res.status_code == 201
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Test Chat"

    # 2. List Sessions
    list_res = await test_client.get("/api/sessions")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # 3. Get Session Detail
    get_res = await test_client.get(f"/api/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 4. Delete Session
    del_res = await test_client.delete(f"/api/sessions/{session_id}")
    assert del_res.status_code == 204


@pytest.mark.asyncio
async def test_chat_endpoint_out_of_scope(test_client: AsyncClient):
    response = await test_client.post(
        "/api/chat",
        json={"message": "How do I make sourdough bread from scratch?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_grounded"] is False
    assert "not covered in Lenny's Podcast transcripts" in data["content"]
