import re
from typing import List, Optional
from src.knowledge.retriever import TranscriptRetriever
from src.knowledge.schemas import TranscriptChunk, Citation
from src.agent.llm_client import BaseLLMClient
from src.agent.schemas import Ship30EssayResponse


SHIP30_SYSTEM_PROMPT = """You are an elite digital writer and growth strategist trained in the Ship 30 for 30 digital writing methodology.

Your mission is to write a comprehensive, publication-grade digital essay (~1,250 words) based STRICTLY on the podcast transcript knowledge provided inside <transcript_context>.

### Ship 30 for 30 Core Writing Principles to Follow:
1. **The Irresistible Hook (1 Sentence)**:
   - Start immediately with a bold, counter-intuitive opening sentence that shatters conventional wisdom.
   - Example: "Most founders think product-led growth is a pricing tier—and that mistake costs them millions."

2. **The 1-3-1 Narrative Cadence (Introduction)**:
   - 1 short sentence hook.
   - 3 rhythmic lines providing tension, context, and the core thesis.
   - 1 punchy transition sentence.

3. **High-Velocity Skimmability**:
   - Organize the body into 3 to 4 modular frameworks/sections with clear H2 headers.
   - Use **selective bold emphasis** on key epiphanies so skimmers can absorb the essay in 30 seconds.
   - Use structured bullet points and numbered takeaways.

4. **Tactical Action Items & Frameworks**:
   - Translate podcast insights into concrete mental models (e.g., LNO Framework, Growth Loops, Founder-Led Review Cadence).
   - Attribute principles directly to the featured experts (e.g., Brian Chesky, Elena Verna, Shreyas Doshi).

5. **Actionable Takeaway (Conclusion)**:
   - End with a single, memorable rule or operational question the reader can apply immediately with their team tomorrow morning.

6. **Target Length**:
   - Deliver an in-depth, thorough essay of approximately 1,250 words. Do not give a shallow summary.

### Source Grounding Rule:
Every factual framework, statistic, or quote MUST originate from the provided <transcript_context>. Do not fabricate external sources.
"""


class Ship30Skill:
    """
    Dedicated skill for generating ~1,250-word Ship 30 for 30 digital essays
    grounded in Lenny's Podcast transcripts.
    """

    def __init__(self, retriever: TranscriptRetriever, llm_client: BaseLLMClient):
        self.retriever = retriever
        self.llm_client = llm_client

    def _assemble_context(self, chunks: List[TranscriptChunk]) -> str:
        """Formats transcript chunks inside secure XML boundary tags."""
        context_parts = []
        for i, c in enumerate(chunks, 1):
            context_parts.append(
                f'<excerpt id="{i}" guest="{c.guest}" episode="{c.episode_title}" timestamp="{c.timestamp_str}">\n'
                f"{c.text}\n"
                f"</excerpt>"
            )
        return "\n\n".join(context_parts)

    async def generate_essay(
        self,
        topic: str,
        guest_filter: Optional[str] = None
    ) -> Ship30EssayResponse:
        """
        Retrieves relevant transcripts, applies Ship 30 writing frameworks,
        and generates a formatted 1,250-word digital essay.
        """
        search_query = f"{topic} {guest_filter}" if guest_filter else topic
        retrieval = self.retriever.retrieve(search_query, top_k=6)

        if not retrieval.is_grounded or not retrieval.chunks:
            # Fallback if no relevant transcripts found
            return Ship30EssayResponse(
                title=f"Topic Not Covered: {topic}",
                hook="This topic is not covered in Lenny's Podcast transcripts.",
                word_count=0,
                markdown_content="### Grounding Notice\nThis topic cannot be generated because there are no supporting transcripts in the Lenny Podcast knowledge base.",
                citations=[]
            )

        context_xml = self._assemble_context(retrieval.chunks)

        user_prompt = f"""<transcript_context>
{context_xml}
</transcript_context>

<user_query>
Write a publication-ready Ship 30 for 30 essay on the following topic:
Topic: "{topic}"
Featured Focus: {guest_filter or 'Relevant Podcast Guests'}
</user_query>

Please produce the complete, formatted Markdown essay adhering to all Ship 30 for 30 principles and target length (~1,250 words). Include the essay title as an # H1 header at the very top."""

        raw_essay = await self.llm_client.generate(
            system_prompt=SHIP30_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.4
        )

        # Extract title from H1 or first line
        lines = raw_essay.strip().splitlines()
        title = topic
        for line in lines:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
                break

        # Extract first non-empty sentence as hook
        hook = ""
        for line in lines:
            cleaned = line.strip().lstrip("#").strip()
            if cleaned and not cleaned.startswith("*") and not cleaned.startswith("-"):
                sentences = re.split(r"(?<=[.!?])\s+", cleaned)
                if sentences:
                    hook = sentences[0]
                    break

        words = len(raw_essay.split())

        return Ship30EssayResponse(
            title=title,
            hook=hook,
            word_count=words,
            markdown_content=raw_essay,
            citations=retrieval.citations
        )
