import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from src.knowledge.retriever import TranscriptRetriever
from src.agent.llm_client import BaseLLMClient
from src.agent.core import LennyGrowthAgent


class MockLLMClient(BaseLLMClient):
    """Mock LLM client returning deterministic responses for testing."""

    def __init__(self, response_text: str = "Brian Chesky advocates for founder-led product reviews."):
        self._response = response_text

    @property
    def model_name(self) -> str:
        return "mock/llama3.2"

    async def generate(self, system_prompt: str, user_prompt: str, temperature: float = 0.3) -> str:
        return self._response


@pytest.fixture
def agent_with_data(tmp_path: Path):
    db_path = str(tmp_path / "sqlite_test_db")
    transcripts_path = tmp_path / "transcripts"
    transcripts_path.mkdir(parents=True, exist_ok=True)

    chesky_file = transcripts_path / "chesky.md"
    chesky_file.write_text("""---
episode_title: "Redesigning Airbnb"
guest: "Brian Chesky"
date: "2023-11-05"
topics: ["founder-led pm", "product reviews"]
---

[00:01:10] Brian Chesky: We combined product marketing with product management and run weekly reviews with Figma prototypes.
""", encoding="utf-8")

    retriever = TranscriptRetriever(
        persist_directory=db_path,
        collection_name="test_agent_collection",
        similarity_threshold=0.30
    )
    retriever.index_directory(str(transcripts_path))
    
    mock_llm = MockLLMClient("Brian Chesky explains that Airbnb combined product marketing with product management.")
    return LennyGrowthAgent(retriever=retriever, llm_client=mock_llm)


@pytest.mark.asyncio
async def test_agent_grounded_response(agent_with_data: LennyGrowthAgent):
    response = await agent_with_data.chat("How does Brian Chesky run product management?")
    
    assert response.is_grounded is True
    assert "Brian Chesky" in response.answer
    assert len(response.citations) > 0
    assert response.citations[0].guest == "Brian Chesky"
    assert response.model_used == "mock/llama3.2"


@pytest.mark.asyncio
async def test_agent_out_of_scope_refusal(agent_with_data: LennyGrowthAgent):
    response = await agent_with_data.chat("How do I bake sourdough bread?")
    
    assert response.is_grounded is False
    assert "not covered in Lenny's Podcast transcripts" in response.answer
    assert len(response.citations) == 0


@pytest.mark.asyncio
async def test_agent_artifact_extraction():
    mock_html = """Here is your interactive ROI calculator:
```html
<!DOCTYPE html>
<html>
<head><title>PLG ROI Calculator</title></head>
<body><h1>Calculator</h1></body>
</html>
```
Hope this helps!"""

    agent = LennyGrowthAgent(
        retriever=TranscriptRetriever(persist_directory="data/test_art_db"),
        llm_client=MockLLMClient(mock_html)
    )
    art_type, art_title, art_content = agent._extract_artifact(mock_html)
    
    assert art_type == "html"
    assert art_title == "PLG ROI Calculator"
    assert "<h1>Calculator</h1>" in art_content
