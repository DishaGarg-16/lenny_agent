# Design Document (UI/UX & Frontend Architecture)
## Project: The Lenny Growth Assistant
**Author:** Forward Deployed Engineer  
**Status:** Approved for Implementation  

---

## 1. UI/UX Principles & Aesthetics

The Lenny Growth Assistant interface is crafted to evoke modern, premium developer-first products (such as Anthropic Claude, Linear, and Vercel). It avoids generic boilerplate styling in favor of high-polish aesthetics, smooth micro-interactions, and a distraction-free two-pane workflow.

### Core Principles
1. **Side-by-Side Dual Pane ("Claude Artifacts" Paradigm):** Conversational chat on the left (or full width when no artifact is present); dynamic, interactive Artifact Viewer sliding out on the right when code, essays, or HTML snippets are generated.
2. **High Visual Polish & Modern Dark/Light Mode:** Deep slate/zinc dark mode (`#0B0F17`) with glassmorphism, subtle glowing borders, and vibrant purple/indigo accent tones (`#6366F1`).
3. **Information Density with Skimmability:** Rich typography (Inter / Plus Jakarta Sans), clear hierarchical headings, interactive citation badges, and formatted callouts.
4. **Instant Visual Feedback:** Smooth streaming indicators, skeleton loaders during RAG retrieval, and real-time status pills for active models (Ollama vs. Cloud).

---

## 2. Information Architecture & Layout Structure

```
+----------------------------------------------------------------------------------------------------+
|  [Logo] Lenny Growth Assistant      [Status: Ollama llama3.2 (Local)]     [Model Switcher v] [New Chat]|
+----------------------------------------------------------------------------------------------------+
|  SIDEBAR           |  CHAT WORKSPACE (50% or 100%)       |  ARTIFACT VIEWER (50% Split Screen)     |
|                    |                                     |                                         |
|  + New Chat        |  [User Bubble]                      |  +-----------------------------------+  |
|                    |  "Write a Ship 30 essay on PLG..."  |  | [Preview] [Raw Code]  [Copy] [X]  |  |
|  Recents:          |                                     |  +-----------------------------------+  |
|  - Brian Chesky PM |  [Assistant Bubble]                 |  | Sandboxed Interactive Preview:    |  |
|  - Retention Loops |  "Here is a 1,250-word essay based  |  |                                   |  |
|  - Onboarding UX   |   on Lenny's transcripts..."        |  | <h1>The 3 Non-Obvious Laws of PLG</h1>|
|                    |                                     |  | <p>Most startups get product-led  |  |
|  [Settings]        |  [Source Chips]:                    |  |   growth completely backwards...</p>|
|  [Health: OK]      |  (Brian Chesky #42) (Elena Verna)   |  |                                   |  |
|                    |                                     |  +-----------------------------------+  |
|                    |  [Input: Ask anything or write...]  |  | (Rendered HTML/CSS or Markdown)   |  |
+--------------------+-------------------------------------+-----------------------------------------+
```

---

## 3. Design System & Design Tokens

### 3.1 Color Palette
```css
:root {
  /* Brand Accents */
  --primary-500: #6366f1;       /* Indigo */
  --primary-600: #4f46e5;
  --primary-glow: rgba(99, 102, 241, 0.25);
  --accent-purple: #8b5cf6;     /* Purple */
  --accent-cyan: #06b6d4;       /* Cyan */
  
  /* Dark Mode Surfaces */
  --bg-app: #090d16;            /* Deep Space Black */
  --bg-surface-1: #0f172a;      /* Slate Card Surface */
  --bg-surface-2: #1e293b;      /* Hover / Active Surface */
  --border-subtle: #1e293b;
  --border-highlight: #334155;
  
  /* Text Tokens */
  --text-main: #f8fafc;
  --text-muted: #94a3b8;
  --text-dim: #64748b;
  
  /* Badges & Status */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
}
```

### 3.2 Typography
* **Primary Font:** Inter, system-ui, -apple-system, sans-serif.
* **Code / Artifact Font:** JetBrains Mono, Fira Code, monospace.
* **Hierarchy:**
  - `H1`: 1.75rem (28px), 700 weight, tight letter-spacing.
  - `H2`: 1.35rem (22px), 600 weight.
  - `H3`: 1.15rem (18px), 600 weight.
  - `Body`: 0.95rem (15px), 1.6 line height.
  - `Caption / Meta`: 0.8rem (13px), 500 weight.

---

## 4. Key Interaction States & Micro-interactions

### 4.1 Idle / Welcome State
* Empty conversation displays prompt starter cards:
  - *"How does Brian Chesky structure founder-led product teams?"*
  - *"Write a Ship 30 for 30 essay on viral B2B loops (Elena Verna)."*
  - *"What are the top 3 retention frameworks mentioned across podcasts?"*
  - *"Generate an interactive HTML/CSS ROI calculator for PLG onboarding."*

### 4.2 Retrieval & Thinking State
* Visual loader pill: `⚡ Searching 150+ Lenny Podcast transcripts...`
* Subtle animated shimmer skeleton on pending message card.

### 4.3 Interactive Citation Badges
* Citations appear as interactive pill badges beneath assistant messages:
  `🏷️ Ep 42: Brian Chesky (00:18:32)`
* **Hover / Click Action:** Opens a tooltip or modal revealing the exact transcript snippet from which the claim was derived.

### 4.4 Side-by-Side Artifact Drawer
* Automatically transitions in from the right edge with smooth 300ms cubic-bezier transition when code or rich essays are detected.
* **Tab Controls:**
  - **Live Preview Tab:** Sandboxed rendered HTML/CSS or styled Markdown view.
  - **Code Tab:** Syntax-highlighted code editor view with line numbers.
  - **Actions Toolbar:** "Copy", "Download File", "Open Fullscreen", and "Close".

---

## 5. Security & Sandboxed Rendering Architecture

Generated HTML/CSS code is rendered using a secure client-side sandbox:
```html
<iframe
  id="artifact-sandbox-frame"
  sandbox="allow-scripts"
  referrerpolicy="no-referrer"
  srcdoc="<sanitized-html-content>"
  style="width: 100%; height: 100%; border: none;"
></iframe>
```
* **Explicit Protection:** Omitting `allow-same-origin` ensures untrusted code cannot access the parent application's cookies, `localStorage`, session tokens, or parent window DOM.
* **Sanitization:** Content is pre-scrubbed with DOMPurify to eliminate malformed scripts or unauthorized external tracking.

---

## 6. Accessibility & Responsive Behavior

* **Keyboard Navigation:** Full keyboard shortcut support (`Cmd/Ctrl + K` to start new chat, `Esc` to close artifact viewer).
* **High Contrast & Screen Reader Support:** Semantic HTML5 tags (`<main>`, `<aside>`, `<nav>`, `<article>`), ARIA labels for all icon buttons.
* **Mobile / Tablet Responsiveness:** Below `1024px`, the split-screen collapses to a tabbed overlay allowing smooth toggling between Chat and Artifact Viewer.