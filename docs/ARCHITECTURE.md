# System Architecture

This document provides a technical breakdown of the architectural components, execution flows, and data boundaries of the AI-LMS platform.

---

## 🗺️ System Component Overview

```
                        +----------------------------+
                        |  Next.js 14 Standalone     |
                        |  React Query / React Flow  |
                        +--------------+-------------+
                                       |
                                       | HTTP REST / Server-Sent Events (SSE)
                                       v
                        +--------------+-------------+
                        |  FastAPI ASGI Gateway API  |
                        |  Slowapi / Structlog       |
                        +-----+--------------+-------+
                              |              |
           +------------------+              +------------------+
           | Relational Queries                                 | Session Overrides / Graph States
           v                                                    v
+----------+------------+                             +---------+----------+
|  PostgreSQL 15 (DB)   |                             |  LangGraph Agent   |
|  SQLAlchemy Async     |                             |  Cognitive Graph   |
+-----------------------+                             +----+----------+----+
                                                           |          |
                                              RAG Search   v          v AI Prompt Completion
                                            +--------------+---+    +-+------------------+
                                            | LlamaIndex RAG   |    | LiteLLM Client     |
                                            | Pinecone / BM25  |    | OpenAI GPT-4o-mini |
                                            +------------------+    +--------------------+
```

The system comprises five core architectural layers:
1. **Presentation Layer (Next.js 14 standalone):** A TypeScript React application utilizing TanStack Query for caching and optimistic UI updates, and React Flow for visual conceptual graphs.
2. **Gateway & Logic Layer (FastAPI):** An asynchronous Python ASGI gateway handling rate limiting, OAuth2 JWT token extraction, and structured logging.
3. **Cognitive Agent Layer (LangGraph):** Orchestrates stateful execution loops, handles conditional transitions, and exposes human-in-the-loop checkpoints (`NodeInterrupt`) for quiz moderation.
4. **Retrieval Layer (LlamaIndex):** Combines Pinecone dense vector queries and BM25 sparse queries, reranked by Cohere, to supply highly relevant chunks to the LLM context.
5. **Persistence & Telemetry Layer (Postgres, Redis, Prometheus, Grafana):** Manages relational states (Postgres), response caching and task queues (Redis), metric collections (Prometheus), and operational dashboards (Grafana).

---

## 📂 Component Boundaries

### 1. Presentation Layer (`/frontend`)
* **Framework:** Next.js 14 configured for `standalone` compilation. Next.js traces files to compile a minimal node runner image, stripping out standard local `node_modules` folders.
* **State Management:** Utilizes `@tanstack/react-query` to decouple server fetches from local components. Implements optimistic updates on progress mutations to check sidebars instantly and rollback on server error.
* **Interactive UI components:**
  * `ConceptMap.tsx`: Embeds a `ReactFlow` viewport. Fetches dynamic node-link lists from `/api/v1/ai/concept-map` and translates them into styled canvas elements.
  * `AIChatPanel.tsx`: A sliding panel querying `/api/v1/ai/chat`. Leverages dynamic streaming reader loops to fetch Server-Sent Events (SSE) tokens chunk-by-chunk.

### 2. Backend API Gateway (`/backend`)
* **Framework:** FastAPI running under Uvicorn. Exposes REST endpoints registered under `/api/v1/` route prefixes. Detailed route descriptors and schemas are available in [API.md](file:///c:/Users/Divyansh%20Aggarwal/.gemini/antigravity-ide/scratch/ai-lms/docs/API.md).
* **Security & Tokens:** Extracted using `get_current_user` OAuth2 dependency. Decodes standard HMAC-SHA256 JWT access/refresh tokens.
* **Rate Limiting:** Exposes `slowapi` rate limit filters configured on AI endpoints, limiting requests to 10 per minute per user key (falling back to client IP).
* **Logging:** Integrated `structlog` to output structured JSON format events.

### 3. Cognitive Agent Pipeline (`/agents`)
* **State Persistence:** Operates a cyclic state graph (`StateGraph`) tracking chat history, active node contexts, generated quizzes, and advisor plans. State checkpoints are saved in memory using an `InMemorySaver`. Detailed node states and human-in-the-loop transition controls are detailed in [AGENTS.md](file:///c:/Users/Divyansh%20Aggarwal/.gemini/antigravity-ide/scratch/ai-lms/docs/AGENTS.md).
* **Nodes:**
  * `Orchestrator Router`: Evaluates intent using structured Pydantic parameters.
  * `Tutor Node`: Feeds RAG citations back into the agent prompt.
  * `Quiz Generator Node`: Halts graph threads using `NodeInterrupt` checkpoints.
  * `Path Advisor Node`: Queries database profiles to construct study schedules.

### 4. RAG Retrieval Pipeline (`/rag`)
* **Chunking Strategy:** `HierarchicalNodeParser` parses documents into a nested hierarchy of 512-token parent nodes and 128-token child nodes.
* **Hybrid Search Retrieval:**
  * **Dense Retrieval:** Submits query vectors to a namespace Pinecone index.
  * **Sparse Retrieval:** Executes a BM25 lookup against a local document store.
  * **Reranking:** Merges vector and keyword hits, reranking them with `CohereRerank` to yield the top 5 nodes. Resolves child nodes to parent nodes before building the LLM context.

### 5. Telemetry & Monitoring Layer (`/docker`)
* **Instrumentation (`backend/app/core/metrics.py`):** Exposes custom metrics scraped by Prometheus on `/metrics`:
  * `lms_llm_latency_seconds`: Histogram measuring response latency.
  * `lms_llm_tokens_total`: Counter tracking prompt and completion tokens.
  * `lms_rag_retrieval_seconds`: Histogram measuring retrieval search times.
  * `lms_active_users`: Gauge tracking concurrent active user sessions.
* **Grafana Integration:** Connects to Prometheus as a data source, rendering visual dashboards from pre-loaded dashboards (`docker/grafana/dashboards/dashboard.json`).
