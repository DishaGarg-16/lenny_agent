import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.knowledge.chunker import parse_frontmatter, parse_dialogue_turns, chunk_transcript


def test_parse_frontmatter():
    sample_md = """---
episode_title: "Test Episode Title"
guest: "Elena Verna"
date: "2023-09-12"
audio_url: "https://example.com"
topics: ["plg", "monetization"]
---

[00:01:00] Elena Verna: This is a test.
"""
    meta, body = parse_frontmatter(sample_md)
    assert meta.episode_title == "Test Episode Title"
    assert meta.guest == "Elena Verna"
    assert meta.date == "2023-09-12"
    assert "plg" in meta.topics
    assert "[00:01:00] Elena Verna: This is a test." in body


def test_parse_dialogue_turns():
    body = """[00:00:10] Lenny Rachitsky: Hello and welcome.
[00:00:25] Brian Chesky: Thanks for having me Lenny."""
    turns = parse_dialogue_turns(body)
    assert len(turns) == 2
    assert turns[0]["speaker"] == "Lenny Rachitsky"
    assert turns[0]["timestamp"] == "00:00:10"
    assert turns[0]["text"] == "Hello and welcome."
    assert turns[1]["speaker"] == "Brian Chesky"
    assert turns[1]["timestamp"] == "00:00:25"
    assert turns[1]["text"] == "Thanks for having me Lenny."


def test_chunk_transcript_file(tmp_path: Path):
    test_file = tmp_path / "test_transcript.md"
    test_file.write_text("""---
episode_title: "Brian Chesky PM"
guest: "Brian Chesky"
date: "2023-11-05"
topics: ["founder-led pm"]
---

[00:00:10] Lenny Rachitsky: Tell us about founder-led product management.
[00:01:10] Brian Chesky: We run product reviews weekly with Figma prototypes.
""", encoding="utf-8")

    chunks = chunk_transcript(test_file, target_chunk_tokens=50, overlap_tokens=10)
    assert len(chunks) >= 1
    assert chunks[0].guest == "Brian Chesky"
    assert chunks[0].episode_title == "Brian Chesky PM"
    assert "Brian Chesky" in chunks[0].text
