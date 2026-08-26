# The Lenny Growth Assistant

A local-first conversational AI and product strategy advisor grounded strictly in Lenny's Podcast transcripts. Built with FastAPI, SQLite/PostgreSQL, React 18, and local Ollama (`llama3.2`), featuring a Claude-style split-screen Artifact Viewer for interactive tools and formatted digital essays.

---

## Table of Contents
1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Key Capabilities](#key-capabilities)
4. [Quickstart Guide](#quickstart-guide)
   - [Method 1: Native Local Execution (Recommended)](#method-1-native-local-execution-recommended)
   - [Method 2: Docker Compose Multi-Container](#method-2-docker-compose-multi-container)
5. [API Endpoints](#api-endpoints)
6. [Security and Sandboxing](#security-and-sandboxing)
7. [Automated Testing](#automated-testing)
8. [Engineering Trade-Offs and Design Decisions](#engineering-trade-offs-and-design-decisions)

---

## System Overview

The Lenny Growth Assistant transforms podcast transcripts into an interactive advisory system. It eliminates hallucinations through mathematical similarity gating, provides source attribution down to the exact timestamp and guest, and extracts generated frameworks into an interactive split-screen viewer.

### Technology Stack
* **LLM Engine**: Local Ollama (`llama3.2` default) with optional Cloud fallback (Claude 3.5 Sonnet / GPT-4o).
* **Vector and Knowledge Store**: Dialogue-aware chunker + SQLite TF-IDF and Subword N-Gram vector engine with metadata topic boosting.
* **Backend API**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Async), Pydantic v2, Uvicorn.
* **Database Layer**: SQLite (local) and PostgreSQL 16 (Docker production).
* **Frontend Web Application**: React 18, Vite, Marked, Lucide Icons, Vanilla CSS design tokens (Royal Emerald theme).
* **Security Layer**: Bleach HTML sanitization, iframe sandboxing, XML boundary prompt protection, and sliding-window rate limiting.

---

## Architecture Diagram

```
+-------------------------------------------------------------------------+
|                        Frontend Web Application                         |
|  - Split-Screen Workspace (Chat Area + Live Artifact Drawer)            |
|  - Interactive Citation Modals [Guest (Timestamp)]                      |
|  - Theme Switcher (Royal Emerald Dark / Light) & Ship 30 Mode Toggle    |
+------------------------------------+------------------------------------+
                                     | (REST API via /api)
                                     v
+-------------------------------------------------------------------------+
|                       FastAPI Backend Gateway                           |
|  - In-Memory Rate Limiter (30 req/min per IP)                           |
|  - LLM Concurrency Semaphore (5 concurrent workers)                     |
|  - XML Prompt Injection Sanitizer                                       |
+-------------------+--------------------------------+--------------------+
                    |                                |
                    v                                v
+------------------------------------+  +---------------------------------+
|      Grounded Agent Engine         |  |   Database & Persistence Layer  |
|  - Anti-Hallucination Gate (>=0.25)|  |  - Async SQLAlchemy 2.0         |
|  - Ship 30 for 30 Skill Engine     |  |  - Sessions, Messages,          |
|  - Claude Artifact Parser (HTML/MD)|  |    Citations, Artifacts         |
+-------------------+----------------+  +---------------------------------+
                    |
                    v
+-------------------------------------------------------------------------+
|              Knowledge Ingestion & Vector Retrieval Engine              |
|  - Dialogue-Aware Sliding Window Chunking (~500 tokens)                 |
|  - SQLite Inverted Index + Cosine Similarity Dot Product                |
|  - Metadata Topic & Guest Name Precision Booster                        |
|  - Curated Transcripts: Chesky, Verna, Doshi, Winters, Alstromer        |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                      Local Ollama Runtime Engine                        |
|  - Model: llama3.2 (Local CPU/GPU inference on port 11434)              |
|  - 180s HTTP timeout for long-form ~1,250 word essay generation         |
+-------------------------------------------------------------------------+
```

---

## Key Capabilities

1. **Strict Source Grounding**: Every answer is derived from verified podcast transcripts. Queries lacking supporting data (e.g., *"How do I make a strawberry milkshake?"*) are rejected deterministically: *"This topic is not covered in Lenny's Podcast transcripts."*
2. **Interactive Citation Badges**: Clickable pills `[Guest (Timestamp)]` display verbatim quotes, episode names, and similarity match scores.
3. **Claude-Style Artifact Viewer**: HTML tools and Markdown essays render in a right-hand slide-out drawer with tabs for Live Preview, Raw Code, Copy to Clipboard, Download File, and Fullscreen.
4. **Ship 30 for 30 Skill**: Generates ~1,250-word structured essays using the 1-3-1 introduction cadence, bold takeaways, and actionable frameworks.

---

## Quickstart Guide

### Prerequisites
* Python 3.12+ (managed via `uv` or standard Python)
* Node.js 18+ & npm
* Ollama installed ([ollama.ai](https://ollama.ai)) with the `llama3.2` model downloaded:
  ```powershell
  ollama pull llama3.2
  ```

---

### Method 1: Native Local Execution (Recommended)

1. **Clone the Repository**:
   ```powershell
   git clone https://github.com/DishaGarg-16/lenny_agent.git
   cd lenny_agent
   ```

2. **Install Backend Dependencies**:
   ```powershell
   uv sync
   # or with pip: pip install -r requirements.txt
   ```

3. **Ingest Transcript Knowledge Base**:
   ```powershell
   uv run python scripts/ingest.py
   ```

4. **Start the FastAPI Backend Server** (Terminal 1):
   ```powershell
   uv run python -m uvicorn src.api.main:app --reload --port 8000
   ```
   * Verify diagnostics at: `http://localhost:8000/health`

5. **Start the React Frontend** (Terminal 2):
   ```powershell
   cd frontend
   npm.cmd install
   npm.cmd run dev
   ```
   * Open the UI at: `http://localhost:3000`

---

### Method 2: Docker Compose Multi-Container

To run the complete multi-container stack (PostgreSQL + FastAPI + React Frontend + Host Ollama Bridge):

```powershell
docker compose up --build
```
* Frontend: `http://localhost:3000`
* Backend API: `http://localhost:8000`
* PostgreSQL: Port `5432`

To shut down:
```powershell
docker compose down
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Diagnostics endpoint checking DB, vector store chunk count, and Ollama status. |
| `GET` | `/api/models` | Lists available local and cloud LLM engines. |
| `POST` | `/api/sessions` | Initializes a new chat session. |
| `GET` | `/api/sessions` | Lists recent conversation sessions. |
| `GET` | `/api/sessions/{id}` | Retrieves session history, citations, and artifacts. |
| `DELETE` | `/api/sessions/{id}` | Deletes a conversation session and cascades. |
| `POST` | `/api/chat` | Grounded conversational RAG endpoint. |
| `POST` | `/api/skills/ship30` | Dedicated Ship 30 for 30 digital essay generator. |
| `GET` | `/api/artifacts/{id}` | Retrieves a generated artifact by ID. |

---

## Security and Sandboxing

* **HTML Sanitization**: Artifacts pass through Bleach sanitizers stripping malicious attributes (`onerror`, `onload`, `javascript:`) before persistence.
* **Iframe Sandbox**: Rendered previews in `ArtifactViewer.jsx` use `sandbox="allow-scripts"` without `allow-same-origin` to isolate host cookies and tokens.
* **XML Boundary Protection**: User inputs escape `<transcript_context>` and `</transcript_context>` tags to prevent system prompt injection.
* **Rate Limiter & Concurrency Lock**: In-memory token bucket limits clients to 30 requests per minute. An async Semaphore limits concurrent inference to 5 streams to prevent RAM/VRAM exhaustion.

---

## Automated Testing

Run the full Pytest test suite across all 7 test modules:

```powershell
uv run pytest
```

### Test Coverage Breakdown:
1. `tests/test_chunking.py`: Dialogue parsing and sliding window chunking.
2. `tests/test_retrieval.py`: SQLite cosine similarity and confidence score gating.
3. `tests/test_database.py`: Async SQLAlchemy CRUD, message cascading, and artifact storage.
4. `tests/test_agent.py`: Grounding, citation extraction, artifact parsing, and out-of-scope refusal.
5. `tests/test_ship30_skill.py`: Ship 30 essay generation, hook extraction, and word counts.
6. `tests/test_api.py`: FastAPI ASGI endpoints (`/health`, `/api/models`, `/api/sessions`, `/api/chat`).
7. `tests/test_security.py`: HTML XSS sanitization, XML injection defense, and rate limiting.

---

## Engineering Trade-Offs and Design Decisions

1. **Local-First Ollama vs. Cloud-Only LLMs**:
   * *Decision*: Default to local Ollama (`llama3.2`) with optional Cloud API keys.
   * *Rationale*: Guarantees zero recurring API costs, complete data privacy, and reliable offline execution on any developer machine.
2. **Pure-Python SQLite Vector Engine vs. Heavy Native C++ Libraries**:
   * *Decision*: Implemented normalized TF-IDF and Subword Bigram vector search backed by SQLite.
   * *Rationale*: Windows SmartApp Control and strict OS policies frequently block unsigned C++ DLLs (such as ChromaDB's `grpcio` or SciPy binary extensions). The pure-Python SQLite engine executes in `< 1ms` with zero native dependencies.
3. **Dialogue-Aware Sliding Window vs. Blind Character Splitting**:
   * *Decision*: Segmented transcripts along natural speaker turns with timestamp metadata rather than fixed character offsets.
   * *Rationale*: Prevents speaker statements from being sliced mid-sentence, preserving context for citations.
4. **Pydantic AI vs. Bulky Agent Frameworks (LangChain / CrewAI / AutoGen)**:
   * *Decision*: Selected Pydantic AI for type-safe structured output validation and schema-driven agent orchestration.
   * *Rationale*: Eliminated the abstraction bloat, breaking deprecation churn, and complex nested wrappers typical of LangChain. Enables native, zero-overhead data sharing with FastAPI and async SQLAlchemy models.
   * *Trade-Off*: Traded off autonomous multi-agent swarm patterns (such as CrewAI/AutoGen multi-turn debate loops) in favor of high-reliability deterministic execution, strict type safety, and fast response times optimal for production RAG and digital essay generation.
