import re
from typing import List, Optional
from src.knowledge.retriever import TranscriptRetriever
from src.knowledge.schemas import TranscriptChunk, Citation
from src.agent.llm_client import BaseLLMClient
from src.agent.schemas import Ship30EssayResponse

SHIP30_SYSTEM_PROMPT = """You are an elite digital writer and growth strategist trained in the Ship 30 for 30 digital writing methodology.

Your mission is to write a comprehensive, publication-grade digital essay (~1,250 words) based STRICTLY on the podcast transcript knowledge provided inside <transcript_context>.

### Ship 30 for 30 Core Writing Principles to Follow:
1. **The Irresistible Hook (1 Sentence)**: Bold, counter-intuitive opening sentence shattering conventional wisdom.
2. **The 1-3-1 Narrative Cadence (Introduction)**: 1 short sentence hook, 3 lines providing tension/context, 1 punchy transition.
3. **High-Velocity Skimmability**: 3 to 4 modular frameworks with clear H2 headers, **selective bold emphasis**, and bullet lists.
4. **Tactical Action Items & Frameworks**: Translate podcast insights into concrete mental models attributed to featured experts.
5. **Actionable Takeaway (Conclusion)**: End with a single, memorable operational rule.
6. **Target Length**: ~1,250 words.

### Source Grounding Rule:
Every factual framework, statistic, or quote MUST originate from the provided <transcript_context>. Do not fabricate external sources.
"""

class Ship30Skill:
    """Dedicated skill for generating ~1,250-word Ship 30 for 30 digital essays grounded in Lenny's Podcast transcripts."""
    def __init__(self, retriever: TranscriptRetriever, llm_client: BaseLLMClient):
        self.retriever = retriever
        self.llm_client = llm_client

    def _assemble_context(self, chunks: List[TranscriptChunk]) -> str:
        """Formats transcript chunks inside secure XML boundary tags."""
        return "\n\n".join([
            f'<excerpt id="{i}" guest="{c.guest}" episode="{c.episode_title}" timestamp="{c.timestamp_str}">\n{c.text}\n</excerpt>'
            for i, c in enumerate(chunks, 1)
        ])

    async def generate_essay(self, topic: str, guest_filter: Optional[str] = None) -> Ship30EssayResponse:
        """Retrieves transcripts, applies Ship 30 frameworks, and generates a formatted 1,250-word digital essay."""
        search_query = f"{topic} {guest_filter}" if guest_filter else topic
        retrieval = self.retriever.retrieve(search_query, top_k=6)
        if not retrieval.is_grounded or not retrieval.chunks:
            return Ship30EssayResponse(
                title=f"Topic Not Covered: {topic}",
                hook="This topic is not covered in Lenny's Podcast transcripts.",
                word_count=0,
                markdown_content="### Grounding Notice\nThis topic cannot be generated because there are no supporting transcripts in the Lenny Podcast knowledge base.",
                citations=[]
            )

        context_xml = self._assemble_context(retrieval.chunks)
        user_prompt = f"""<transcript_context>\n{context_xml}\n</transcript_context>\n\n<user_query>\nWrite a publication-ready Ship 30 for 30 essay on:\nTopic: "{topic}"\nFeatured Focus: {guest_filter or 'Relevant Podcast Guests'}\n</user_query>\n\nProduce the complete, formatted Markdown essay (~1,250 words). Include the essay title as an # H1 header at the very top."""

        raw_essay = await self.llm_client.generate(system_prompt=SHIP30_SYSTEM_PROMPT, user_prompt=user_prompt, temperature=0.4)
        lines = raw_essay.strip().splitlines()
        title = topic
        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break

        hook = ""
        for line in lines:
            cleaned = line.strip().lstrip("#").strip()
            if cleaned and not cleaned.startswith("*") and not cleaned.startswith("-"):
                sentences = re.split(r"(?<=[.!?])\s+", cleaned)
                if sentences:
                    hook = sentences[0]
                    break

        return Ship30EssayResponse(
            title=title, hook=hook, word_count=len(raw_essay.split()),
            markdown_content=raw_essay, citations=retrieval.citations
        )
