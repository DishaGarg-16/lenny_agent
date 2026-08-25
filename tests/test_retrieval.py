import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.knowledge.retriever import TranscriptRetriever


@pytest.fixture
def test_retriever(tmp_path: Path):
    db_path = str(tmp_path / "sqlite_test_db")
    transcripts_path = tmp_path / "transcripts"
    transcripts_path.mkdir(parents=True, exist_ok=True)

    sample_transcript = transcripts_path / "elena.md"
    sample_transcript.write_text("""---
episode_title: "PLG Mastery"
guest: "Elena Verna"
date: "2023-09-12"
topics: ["plg", "viral loops"]
---

[00:00:20] Lenny Rachitsky: Tell us about B2B viral loops.
[00:01:45] Elena Verna: Product-led growth is an organizational operating model where the product acquires, activates, monetizes, and retains users. Inherent virality is when using the product requires sending an artifact to someone else like Calendly or DocuSign.
""", encoding="utf-8")

    retriever = TranscriptRetriever(
        persist_directory=db_path,
        collection_name="test_collection",
        similarity_threshold=0.40
    )
    retriever.index_directory(str(transcripts_path))
    return retriever


def test_retriever_indexing_and_query(test_retriever):
    assert test_retriever.count() > 0

    # In-domain relevant query
    result = test_retriever.retrieve("How does Elena Verna define PLG viral loops?", top_k=2)
    assert result.is_grounded is True
    assert len(result.citations) > 0
    assert result.citations[0].guest == "Elena Verna"
    assert "Elena Verna" in result.chunks[0].speaker or "Elena Verna" in result.chunks[0].text
    assert result.top_score >= 0.40


def test_retriever_out_of_scope_query(test_retriever):
    # Completely unrelated query
    result = test_retriever.retrieve("What temperature do I bake sourdough bread at in the oven?", top_k=2, threshold=0.65)
    assert result.is_grounded is False
