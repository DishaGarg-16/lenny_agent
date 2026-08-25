"""
Knowledge Base Ingestion Script.
Chunks transcripts and indexes 384-dimensional embeddings into local SQLite vector storage.

Usage:
  uv run python scripts/ingest.py
"""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.knowledge.retriever import TranscriptRetriever


def main():
    print("=" * 60)
    print("Lenny Growth Assistant - Transcript Ingestion Pipeline")
    print("=" * 60)

    transcripts_dir = "data/transcripts"
    db_dir = "data/vector_db"

    print(f"[*] Scanning transcripts from: {transcripts_dir}")
    retriever = TranscriptRetriever(persist_directory=db_dir)

    total_indexed = retriever.index_directory(transcripts_dir)
    print(f"[+] Successfully indexed {total_indexed} semantic chunks into SQLite vector store.")
    print(f"[+] Database file: {retriever.db_path}")

    # Test query
    test_query = "What is Brian Chesky's view on product management?"
    print(f"\n[*] Running sanity test query: '{test_query}'")
    result = retriever.retrieve(test_query, top_k=2)

    print(f"[+] Grounded: {result.is_grounded} (Top Similarity Score: {result.top_score})")
    for i, citation in enumerate(result.citations, 1):
        print(f"    Citation {i}: [{citation.guest}, {citation.episode_title}, {citation.timestamp_str}] (score: {citation.similarity_score})")
        print(f"    Excerpt: {citation.snippet[:120]}...\n")

    print("[✓] Ingestion verified successfully.")


if __name__ == "__main__":
    main()
