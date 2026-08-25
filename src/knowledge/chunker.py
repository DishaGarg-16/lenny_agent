import re
from pathlib import Path
from typing import List, Tuple
from .schemas import TranscriptMetadata, TranscriptChunk


def parse_frontmatter(content: str) -> Tuple[TranscriptMetadata, str]:
    """
    Extracts YAML-style frontmatter from transcript markdown content.
    Returns (TranscriptMetadata, remaining_body_text).
    """
    frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
    if not frontmatter_match:
        # Fallback if no frontmatter header is present
        metadata = TranscriptMetadata(
            episode_title="Lenny's Podcast Transcript",
            guest="Unknown Guest",
            date=None,
            audio_url=None,
            topics=[]
        )
        return metadata, content.strip()

    yaml_block = frontmatter_match.group(1)
    body_text = frontmatter_match.group(2).strip()

    # Parse simple key-value pairs from YAML frontmatter
    data = {}
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                # Parse list of topics
                topics_raw = val[1:-1]
                data[key] = [t.strip().strip('"').strip("'") for t in topics_raw.split(",") if t.strip()]
            else:
                data[key] = val

    metadata = TranscriptMetadata(
        episode_title=data.get("episode_title", "Lenny's Podcast"),
        guest=data.get("guest", "Unknown Guest"),
        date=data.get("date"),
        audio_url=data.get("audio_url"),
        topics=data.get("topics", [])
    )
    return metadata, body_text


def parse_dialogue_turns(body_text: str) -> List[dict]:
    """
    Splits body text into individual dialogue turns based on timestamp markers:
    e.g. `[00:01:10] Brian Chesky: Thanks Lenny...`
    """
    pattern = r"\[(\d{1,2}:\d{2}(?::\d{2})?)\]\s*([^:\n]+):\s*"
    matches = list(re.finditer(pattern, body_text))

    if not matches:
        # If no timestamp turns found, treat entire text as single turn
        return [{
            "timestamp": "00:00:00",
            "speaker": "Speaker",
            "text": body_text.strip()
        }]

    turns = []
    for i, match in enumerate(matches):
        timestamp = match.group(1)
        speaker = match.group(2).strip()
        start_idx = match.end()
        end_idx = matches[i + 1].start() if i + 1 < len(matches) else len(body_text)
        turn_text = body_text[start_idx:end_idx].strip()
        if turn_text:
            turns.append({
                "timestamp": timestamp,
                "speaker": speaker,
                "text": turn_text
            })

    return turns


def chunk_transcript(
    file_path: Path,
    target_chunk_tokens: int = 500,
    overlap_tokens: int = 100
) -> List[TranscriptChunk]:
    """
    Loads a transcript file, extracts metadata, and generates structured semantic chunks
    preserving speaker labels and timestamp attribution.
    """
    content = file_path.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(content)
    turns = parse_dialogue_turns(body)

    # Approximate token count: 1 token ~= 4 characters or 0.75 words
    def approx_token_count(text: str) -> int:
        return max(1, len(text.split()))

    chunks: List[TranscriptChunk] = []
    current_turns = []
    current_tokens = 0
    chunk_index = 0

    for turn in turns:
        turn_token_count = approx_token_count(turn["text"])
        current_turns.append(turn)
        current_tokens += turn_token_count

        if current_tokens >= target_chunk_tokens:
            # Construct chunk text combining speaker dialogue
            combined_lines = [
                f"[{t['timestamp']}] {t['speaker']}: {t['text']}"
                for t in current_turns
            ]
            chunk_text = "\n\n".join(combined_lines)
            primary_timestamp = current_turns[0]["timestamp"]
            primary_speaker = current_turns[0]["speaker"]

            chunk_id = f"{metadata.guest.lower().replace(' ', '_')}_{chunk_index:03d}"
            chunks.append(TranscriptChunk(
                chunk_id=chunk_id,
                episode_title=metadata.episode_title,
                guest=metadata.guest,
                timestamp_str=primary_timestamp,
                speaker=primary_speaker,
                text=chunk_text,
                topics=metadata.topics
            ))
            chunk_index += 1

            # Retain overlap turns for continuity
            overlap_count = 0
            overlap_turns = []
            for t in reversed(current_turns):
                t_tokens = approx_token_count(t["text"])
                if overlap_count + t_tokens <= overlap_tokens:
                    overlap_turns.insert(0, t)
                    overlap_count += t_tokens
                else:
                    break

            current_turns = overlap_turns
            current_tokens = sum(approx_token_count(t["text"]) for t in current_turns)

    # Add any remaining turns as final chunk
    if current_turns:
        combined_lines = [
            f"[{t['timestamp']}] {t['speaker']}: {t['text']}"
            for t in current_turns
        ]
        chunk_text = "\n\n".join(combined_lines)
        primary_timestamp = current_turns[0]["timestamp"]
        primary_speaker = current_turns[0]["speaker"]

        chunk_id = f"{metadata.guest.lower().replace(' ', '_')}_{chunk_index:03d}"
        chunks.append(TranscriptChunk(
            chunk_id=chunk_id,
            episode_title=metadata.episode_title,
            guest=metadata.guest,
            timestamp_str=primary_timestamp,
            speaker=primary_speaker,
            text=chunk_text,
            topics=metadata.topics
        ))

    return chunks
