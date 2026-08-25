import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.knowledge.retriever import TranscriptRetriever
from src.agent.llm_client import BaseLLMClient
from src.agent.skills.ship30 import Ship30Skill


class MockShip30LLMClient(BaseLLMClient):
    @property
    def model_name(self) -> str:
        return "mock/ship30"

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        return """# The 3 Non-Obvious Laws of B2B Product-Led Growth

Most founders think product-led growth is just a self-serve checkout page.

They are completely wrong.
PLG is not a go-to-market trick.
It is an operating model.

Here are the 3 core frameworks from Elena Verna:

## 1. Monetize the Value, Not the Onboarding
Allow users to experience the "Aha!" moment before gating features.

## 2. Inherent vs Collaboration Virality
Collaboration loops beat refer-a-friend buttons.

## 3. Actionable Takeaway
Look at your product qualified leads tomorrow morning."""


@pytest.fixture
def ship30_skill(tmp_path: Path):
    db_path = str(tmp_path / "sqlite_test_db")
    transcripts_path = tmp_path / "transcripts"
    transcripts_path.mkdir(parents=True, exist_ok=True)

    elena_file = transcripts_path / "elena.md"
    elena_file.write_text("""---
episode_title: "PLG Mastery"
guest: "Elena Verna"
date: "2023-09-12"
topics: ["plg", "viral loops"]
---

[00:01:45] Elena Verna: PLG is not a go-to-market tactic; it is an organizational operating model where the product acquires, activates, monetizes, and retains users.
""", encoding="utf-8")

    retriever = TranscriptRetriever(
        persist_directory=db_path,
        collection_name="test_ship30_collection",
        similarity_threshold=0.30
    )
    retriever.index_directory(str(transcripts_path))
    
    mock_llm = MockShip30LLMClient()
    return Ship30Skill(retriever=retriever, llm_client=mock_llm)


@pytest.mark.asyncio
async def test_ship30_essay_generation(ship30_skill: Ship30Skill):
    essay = await ship30_skill.generate_essay("Product-Led Growth", guest_filter="Elena Verna")
    
    assert essay.title == "The 3 Non-Obvious Laws of B2B Product-Led Growth"
    assert "Most founders think" in essay.hook
    assert essay.word_count > 30
    assert len(essay.citations) > 0
    assert essay.citations[0].guest == "Elena Verna"
    assert "## 1. Monetize the Value" in essay.markdown_content
