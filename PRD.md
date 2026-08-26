# Product Requirements: The Lenny Growth Assistant

## 1. Overview
The Lenny Growth Assistant is a conversational AI web application designed for Product Managers, Growth Leads, Founders, and Operators. It transforms 200+ hours of transcripts from *Lenny's Podcast* into a reliable, grounded knowledge assistant.

Users can:
1. Ask nuanced product, growth, leadership, and operational questions and receive answers strictly grounded in podcast knowledge with precise episode/guest citations.
2. Generate structured, publication-grade written artifacts—notably **"Ship 30 for 30"** style growth essays (~1,250 words) adhering to proven digital writing principles.
3. View and interact with generated Markdown, HTML, and CSS artifacts live in a split-screen in-app viewer (similar to Claude Artifacts) with secure sandboxing.
4. Seamlessly run on a 100% free, local-first stack using **Ollama** (`llama3.2`), with an optional cloud model toggle for enterprise evaluators.

---

## 2. Target Users & Problem Statement

| Persona | Primary Job-To-Be-Done (JTBD) | Pain Points Removed |
| :--- | :--- | :--- |
| **Product Manager (PM)** | Finding actionable frameworks on product-market fit, user onboarding, PRDs, and roadmapping from top tech leaders (e.g., Brian Chesky, Shreyas Doshi). | Eliminates hours of scrubbing through podcast episodes and searching generic internet summaries. |
| **Growth Lead / Marketer** | Identifying validated B2B/B2C growth loops, pricing strategies, retention tactics, and distribution channels. | Eliminates generic LLM hallucinations; replaces vague advice with battle-tested tactical examples. |
| **Founder / Operator** | Creating high-impact internal documentation, leadership memos, and growth essays to share with teams and stakeholders. | Eliminates manual drafting; generates formatted, publication-ready essays grounded in expert insights. |

### 2.2 Core Value Proposition
> *"Turn expert podcast wisdom into grounded answers, actionable essays, and live-rendered artifacts in seconds—without prompt engineering, cloud costs, or risk of hallucination."*

---

## 3. Success Metrics

### 3.1 Product Quality & AI Performance
* **Grounding Precision & Source Attribution:** 100% of factual claims in generated answers must provide verifiable citations (Episode Title, Guest Name, and approximate Timestamp/Context).
* **Hallucination Rate (Out-of-Scope Queries):** 0% ungrounded responses. If a user asks a question not covered in the transcript corpus (e.g., *"How do I bake sourdough bread?"*), the system must explicitly acknowledge the lack of coverage rather than fabricate an answer.
* **Ship 30 for 30 Essay Quality:** Generated essays must adhere to a target length of ~1,250 words, featuring a captivating hook, 1-3-1 rhythmic cadence, bolded skim-friendly takeaways, and clear tactical action items.
* **Retrieval Relevance & Grounding Gate:** Calibrated similarity threshold gating (`>= 0.25`) enforcing deterministic refusal for out-of-scope queries while ensuring high recall for concise 3-word topic prompts.
* **Rate Limiting & Concurrency Defense:** In-memory sliding window rate limiter (30 req/min per IP) and an async concurrency queue (5 simultaneous streams) preventing RAM/VRAM exhaustion.

### 3.2 Operational & Technical Readiness
* **Local-First Latency:** End-to-end response generation on local Ollama (`llama3.2`) under **4 seconds** for initial token response.
* **Zero Cloud Cost & Zero Setup Barrier:** 100% functional out-of-the-box using local Ollama and local PostgreSQL with zero credit cards, paid API keys, or cloud dependencies.
* **Deployment Reproducibility:** Single-command startup via `docker-compose up` or local virtualenv script.
* **Security & Isolation:** 100% of untrusted HTML artifacts isolated in an iframe sandbox without parent DOM or cookie access.

---

## 4. Explicit Assumptions & Scope Boundaries

### 4.1 Assumptions
1. **Transcript Data Source:** Transcripts are sourced from Lenny's publicly available podcast/newsletter transcript repository in text/markdown/json format.
2. **Target Hardware:** The evaluator runs the demo on a modern laptop/desktop (Windows, macOS, or Linux) with Ollama installed locally.
3. **Model Selection:** Local execution uses lightweight, high-performance models (e.g., Meta `llama3.2:1b`/`llama3.2:3b` or `mistral:7b`), ensuring fast local CPU/GPU execution without exceeding 4GB VRAM.
4. **Single-Tenant Operational Model:** Designed as a high-trust internal product/growth assistant with session-based isolation.

### 4.2 Scope Choices (Included vs. Excluded)

| In Scope (Included) | Out of Scope (Intentionally Excluded) | Rationale |
| :--- | :--- | :--- |
| **Grounded RAG** | Real-time audio transcription | Curated transcripts provide higher fidelity without audio GPU latency. |
| **Ship 30 Essay Generator** | Complex multi-tenant enterprise RBAC | Single-tenant session isolation is optimal for internal growth advisory. |
| **Split-Screen Artifact Viewer** | Paid cloud vector databases (Pinecone/Qdrant) | Pure-Python SQLite vector store is 100% free, private, and portable. |
| **Local Ollama + Cloud Switch** | Multi-agent autonomous debate swarms | Deterministic schema validation guarantees reliable output quality. |
| **PostgreSQL / SQLite Persistence** | Production audio streaming infrastructure | Text transcripts eliminate external network dependencies. |
| **Iframe Sandbox & Rate Limiting** | Custom proprietary model training | Off-the-shelf local models (`llama3.2`) with RAG provide higher accuracy. |
| **Automated Test Suite (18 tests)** | Paid proprietary cloud analytics suites | Local structured logging and `/health` diagnostics provide full observability. |

---

## 5. Adversarial Input & Risk Management

| Risk / Threat | Severity | Mitigation Strategy |
| :--- | :--- | :--- |
| **Prompt Injection & Jailbreaks** | High | User inputs and retrieved context chunks are isolated inside strict XML boundary tags (`<transcript_context>`, `<user_query>`). The system prompt instructs the model to treat input within tags strictly as data, never as instructions. |
| **Malicious HTML Artifacts (XSS)** | Critical | Rendered HTML artifacts are hosted inside an `<iframe sandbox="allow-scripts">` element omitting `allow-same-origin`. Sanitization via `DOMPurify` / `bleach` strips `onerror`, `onload`, inline script injection, and `javascript:` URIs. |
| **Hallucination on Unknown Queries** | High | Embedding similarity threshold gating: If retrieved context confidence is `< 0.25`, the agent returns a standard grounded refusal: *"This topic is not covered in Lenny's Podcast transcripts."* |
| **Service Outages (Ollama / Cloud LLM)** | Medium | FastAPI resilience layer with timeout detection, health endpoint monitoring, and user-friendly error banners in the UI. |
| **Database Injection (SQLi)** | High | SQLAlchemy ORM parameterized queries used across all session and message persistence layers. |

---

## 6. Key User Flows & Functional Requirements

```mermaid
flowchart TD
    User([User]) -->|1. Opens App| UI[Lenny Growth Assistant Web UI]
    UI -->|2. Selects Model| Toggle[Ollama local / Cloud toggle]
    UI -->|3. Submits Query or Skill Request| API[FastAPI Gateway]
    
    API -->|4. Retrieve Context| RAG[Vector Search / Embeddings]
    RAG -->|5. Return Ranked Chunks| Engine[Agent Orchestration Engine]
    
    Engine -->|6. Context + Guardrails| LLM[Ollama llama3.2 / Cloud]
    LLM -->|7. Stream / Complete Response| Engine
    
    Engine -->|8a. Standard Answer + Citations| UI
    Engine -->|8b. Detect Artifact Markdown/HTML| Viewer[Claude-style Split Screen Viewer]
    
    API -->|9. Persist Session & History| DB[(PostgreSQL Database)]
```

### Flow 1: Grounded Conversational Q&A
* **Trigger:** User asks a conceptual or tactical question (e.g., *"What is Brian Chesky's advice on founder-led product management?"*).
* **Process:** Vector search retrieves the top relevant transcript passages; the agent synthesizes the response quoting the guest and linking the episode.
* **Output:** Answer with interactive citation chips indicating episode name and context.

### Flow 2: Ship 30 for 30 Growth Essay Generation
* **Trigger:** User asks for an essay, guide, or clicks the *"Write a Ship 30 for 30 Essay"* action chip.
* **Process:** The dedicated Ship 30 skill structures the grounded knowledge into:
  - Strong, provocative hook
  - 1-3-1 cadence introduction
  - 3–5 core tactical sections with bolded headers and punchy bullets
  - Actionable concluding takeaway
  - Word count target ~1,250 words
* **Output:** Full essay rendered both in chat and automatically extracted into the Artifact Viewer.

### Flow 3: Interactive Artifact Generation & Live Preview
* **Trigger:** Assistant generates an HTML/CSS landing page snippet, interactive calculator, or structured markdown framework.
* **Process:** Frontend detects artifact code blocks (````html ... ```` or ````markdown ... ````), slides open the side-by-side Artifact Drawer, and renders the sandboxed live preview.
* **User Controls:** Live Preview tab, Raw Code tab, Copy to Clipboard, Fullscreen toggle, and Download.
