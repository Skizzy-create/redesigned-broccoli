# Smart Document Q&A System

Upload PDFs and DOCX files, ask natural language questions, get answers grounded in the document content. Supports multi-turn conversations with follow-up questions.

Built with FastAPI, PostgreSQL, Celery + Redis, FAISS vector search, Sentence Transformers, and OpenAI API (with optional Gemini compatibility).

---

## How to Start

Primary validation and release verification in this project are Docker-first.

### Option 1: Docker (recommended for beginners)

Use this if you want everything to run with one command.

1. Open terminal in this project folder.
2. Run:

```bash
docker compose up --build
```

This starts PostgreSQL + Redis + Celery worker + API server and runs migrations automatically.

API URL: **http://localhost:8000**

Stop all services:

```bash
docker compose down
```

### Option 2: Local Development with Conda (no Docker)

Use this if you want to run each service manually.

You need:
1. Python 3.12
2. Conda (Miniconda or Anaconda)
3. Local PostgreSQL and Redis running

#### Windows PowerShell (copy-paste)

```powershell
# 1) Create and activate environment
conda create -p .conda python=3.12 -y
conda activate .\.conda

# 2) Install app + dev dependencies
python -m pip install -e ".[dev]"

# 3) Create .env from template
Copy-Item .env.example .env

# 4) Edit .env with your values
#    - DATABASE_URL (your local Postgres)
#    - API_KEY
#    - OPENAI_API_KEY (or Gemini values if using Gemini)

# 5) Run migrations
alembic upgrade head
```

Start worker and API in two separate terminals (same activated conda env):

```powershell
# Terminal A
conda activate .\.conda
celery -A app.queue.celery_app:celery_app worker --loglevel=INFO --pool=solo
```

```powershell
# Terminal B
conda activate .\.conda
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API URL: **http://127.0.0.1:8000**

#### macOS/Linux (copy-paste)

```bash
# 1) Create and activate environment
conda create -p .conda python=3.12 -y
conda activate ./.conda

# 2) Install app + dev dependencies
python -m pip install -e ".[dev]"

# 3) Create .env from template
cp .env.example .env

# 4) Edit .env with your values, then run migrations
alembic upgrade head
```

### What to Open After Starting

| URL | What it is |
|-----|------------|
| http://localhost:8000/docs | Swagger UI - interactive API docs with "Try it out" |
| http://localhost:8000/ui | Testing Console - browser UI for uploading files and asking questions |
| http://localhost:8000/ui/docs | Architecture Docs - component-level system overview |
| http://localhost:8000/openapi.json | Raw OpenAPI spec |

---

## Testing Console (Browser UI)

Go to **http://localhost:8000/ui** after starting the server.

The UI lets you do everything without cURL or Postman:

1. **Health Check** - verify the API and database are running
2. **Upload a Document** - drag or select a PDF/DOCX file, see the task ID returned
3. **Check Task Status** - paste the task ID, poll until ingestion is complete
4. **Ask a Question** - select a document, type a question, get an answer with source citations
5. **Follow-up Questions** - continue the conversation using the returned conversation ID

The UI auto-fills your API key and presents JSON responses in a readable format.

There's also **http://localhost:8000/ui/docs** which shows the internal architecture: what each component does, where it lives in the codebase, and how the pieces connect.

---

## Configuration

Copy `.env.example` to `.env` and fill in the values that matter:

```bash
cp .env.example .env
```

**Required:**

| Variable | What it does | Default |
|----------|-------------|---------|
| `API_KEY` | Auth key for all API requests (sent as `X-API-Key` header) | `your-secret-api-key` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://smartdoc:smartdoc@db:5432/smartdocqa` |

**LLM (OpenAI required, Gemini optional):**

| Variable | What it does |
|----------|-------------|
| `LLM_PROVIDER` | `openai` (default) or `gemini` |
| `OPENAI_API_KEY` | Your OpenAI key (required when `LLM_PROVIDER=openai`) |
| `OPENAI_MODEL` | Model name, e.g. `gpt-4o-mini` |
| `GEMINI_API_KEY` | Your Gemini key (optional fallback) |
| `GEMINI_MODEL` | Model name, e.g. `gemini-2.5-flash` |

**Background tasks:**

| Variable | What it does | Default |
|----------|-------------|---------|
| `CELERY_BROKER_URL` | Celery broker URL | `redis://redis:6379/0` |
| `CELERY_RESULT_BACKEND` | Celery result backend URL | `redis://redis:6379/1` |

If no LLM key is set, the system still works — it returns the best-matching document chunks instead of a generated answer.

**Optional tuning:**

| Variable | Default | Purpose |
|----------|---------|---------|
| `CHUNK_SIZE_TOKENS` | `512` | How big each text chunk is |
| `CHUNK_OVERLAP_TOKENS` | `64` | Overlap between chunks |
| `TOP_K_RETRIEVAL` | `20` | Candidates pulled from vector search |
| `TOP_N_RERANK` | `5` | Final chunks after cross-encoder reranking |
| `MAX_UPLOAD_SIZE_MB` | `50` | Max file size |
| `MAX_WORKERS` | `4` | Background ingestion workers |

---

## API Reference

All API routes require the header: `X-API-Key: <your-api-key>`

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/v1/health` | No | Basic liveness check |
| GET | `/api/v1/health/ready` | No | Readiness check (includes DB) |

### Documents

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/documents` | Upload a PDF or DOCX file |
| GET | `/api/v1/documents` | List all documents |
| GET | `/api/v1/documents/{document_id}` | Get document details and status |
| DELETE | `/api/v1/documents/{document_id}` | Delete a document and its index |
| POST | `/api/v1/documents/{document_id}/ask` | Ask a question about a document |

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/tasks/{task_id}` | Check ingestion task progress |

### Conversations

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/conversations` | List all conversations |
| GET | `/api/v1/conversations/{conversation_id}` | Get conversation with message history |
| POST | `/api/v1/conversations/{conversation_id}/ask` | Ask a follow-up question |
| DELETE | `/api/v1/conversations/{conversation_id}` | Delete a conversation |

---

## Complete Usage Flow (cURL)

Here's the full workflow from upload to multi-turn Q&A:

**Step 1: Check health**

```bash
curl http://127.0.0.1:8000/api/v1/health
```

**Step 2: Upload a document**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents \
  -H "X-API-Key: your-secret-api-key" \
  -F "file=@sample_docs/company_policy.pdf"
```

Response includes `document_id` and `task_id`. Save both.

**Step 3: Wait for ingestion to finish**

```bash
curl http://127.0.0.1:8000/api/v1/tasks/{task_id} \
  -H "X-API-Key: your-secret-api-key"
```

Repeat until `status` is `completed`. Progress goes 5% -> 25% -> 45% -> 65% -> 80% -> 100%.

**Step 4: Ask a question**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/documents/{document_id}/ask \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the company leave policy?"}'
```

Response includes the `answer`, `sources` with page numbers, and a `conversation_id`.

**Step 5: Ask a follow-up**

```bash
curl -X POST http://127.0.0.1:8000/api/v1/conversations/{conversation_id}/ask \
  -H "X-API-Key: your-secret-api-key" \
  -H "Content-Type: application/json" \
  -d '{"question": "How many days of sick leave specifically?"}'
```

The system uses conversation history to resolve context for follow-up questions.

If retrieval confidence is low, the API can return:

- `status: needs_more_context`
- `needs_more_context: true`
- `clarifying_question: ...`

This indicates the assistant is asking for a narrower question (section, timeframe, entity, or quote) before continuing.

---

## How RAG and Fetching Work

The question-answering pipeline is iterative:

1. Query preparation
- Follow-up questions are rewritten into a more explicit retrieval query.

2. Retrieval
- Semantic retrieval (FAISS embeddings) and lexical retrieval (BM25) are combined.
- Reciprocal rank fusion merges both result sets.

3. Reranking
- A cross-encoder reranker scores the fused candidates.
- Top chunks are selected for generation.

4. Multi-cycle refinement
- If confidence is below threshold, retrieval runs another cycle with a refined query.
- Maximum cycles are configurable via `RAG_MAX_CYCLES`.

5. Answer or clarification
- If confidence is sufficient, the LLM returns a grounded answer with sources.
- If not, API returns `needs_more_context` and a targeted clarifying question.

---

## Postman Collection

Ready-to-import files in `postman/`:

- `Smart-Document-QA.postman_collection.json` — all endpoints with auto-save scripts
- `Smart-Document-QA.local.postman_environment.json` — local environment variables

**How to use:**

1. Open Postman, click Import, drag in both JSON files
2. Select the `Smart Document QA Local` environment (top-right dropdown)
3. Run `Health` first to verify connectivity
4. Run `Upload Document` — it auto-saves `documentId` and `taskId` to environment variables
5. Run `Get Task Status` until ingestion completes
6. Run `Ask Document` — auto-saves `conversationId`
7. Run `Ask Follow-up` to continue the conversation

---

## Sample Documents

3 upload-ready files in `sample_docs/`:

- `company_policy.pdf`
- `async_programming_guide.pdf`
- `quarterly_report_q1_2026.docx`

Full descriptions and suggested questions: `sample_docs/README.md`

---

## Running Tests

```bash
# If needed, activate environment first
# Windows PowerShell: conda activate .\.conda
# macOS/Linux:       conda activate ./.conda

# Install dev dependencies (first time only)
python -m pip install -e ".[dev]"

# Run all tests
python -m pytest

# Run in current default mode from config (verbose)
python -m pytest
```

Tests use SQLite in-memory — no PostgreSQL needed. Current suite:

- Configuration and enum validation
- Task queue lifecycle and worker pool behavior
- Database model constraints and cascade deletes
- Health endpoints (liveness + readiness)
- Document endpoints (upload, list, get, ask, delete)
- Conversation endpoints (list, get, follow-up, delete)
- UI routes (testing console, architecture docs, favicon)

For enterprise testing policy and route-level coverage details, see:

- `docs/TEST_COVERAGE.md`

---

## Enterprise Quality Standards

This project uses strict quality and release standards:

1. API-first contract discipline
- Public routes are explicitly versioned under `/api/v1`.
- Request/response envelopes are consistent for success and error states.

2. Reliability and failure handling
- Async ingestion is isolated in a Celery worker process.
- Upload API remains non-blocking (`202 Accepted`) and progress is polled via task endpoint.
- Parser, queue, and provider failures are surfaced with typed API errors.

3. Security and operational hygiene
- All API routes enforce API-key authentication except health checks.
- Structured request logging includes request IDs for traceability.
- Dockerized runtime isolates app, worker, DB, and broker.

4. Release quality gates
- Static diagnostics clean on changed files.
- Automated tests must pass.
- Docker compose configuration must validate and all required services must start.

---

## Docker-Only Validation Workflow

If you want zero local dependency setup, use Docker only:

```bash
docker compose up -d --build
docker compose ps
```

Then validate key endpoints:

```bash
curl -H "X-API-Key: your-secret-api-key" http://127.0.0.1:8000/api/v1/health
```

Upload and task polling can be done via Postman collection or cURL.

---

## Postman Audit Status

The collection in `postman/Smart-Document-QA.postman_collection.json` is aligned with implemented routes:

- Health and readiness
- Document upload/list/get/ask/delete
- Task status polling
- Conversation list/get/follow-up/delete
- Optional UI open endpoint

Environment file: `postman/Smart-Document-QA.local.postman_environment.json`

Before running collection requests, ensure `apiKey` matches `API_KEY` from deployment environment.

---

## Why First Docker Build Is Slow

The first build can take significant time due to dependency installation, especially machine-learning libraries (PyTorch and sentence-transformers).

Expected behavior:

1. First build is the slowest (dependency download + image layer creation).
2. Subsequent builds are much faster when requirements and base layers are cached.
3. First ingestion task in a fresh environment can also be slower due to model initialization.

---

## Design Decisions

**Why Celery + Redis for background processing?**
The assignment explicitly requires Celery + Redis. Upload requests return immediately with `202 Accepted` while ingestion runs in a worker process, and `/api/v1/tasks/{task_id}` provides progress polling.

**Why hybrid retrieval (FAISS + BM25) instead of just vector search?**
Pure semantic search misses exact keyword matches (names, codes, acronyms). BM25 catches those. Reciprocal rank fusion combines both result sets. A cross-encoder reranker (ms-marco-MiniLM-L6-v2) then scores the merged candidates for final selection.

**Why OpenAI-compatible abstraction for both providers?**
Gemini exposes an OpenAI-compatible endpoint. One client class handles both OpenAI and Gemini through the same interface — just different base URLs and keys. Adding a new provider means adding a config block, not a new client.

**Why no streaming responses?**
The API returns complete answers. Streaming adds SSE/WebSocket complexity that wasn't required. The retrieval + generation pipeline typically responds in 2-5 seconds.

**What happens when there's no LLM key configured?**
The system falls back to returning the top-ranked document chunks directly. You still get useful results — just not a synthesized answer.

**What happens when the answer isn't in the document?**
The LLM prompt explicitly instructs the model to say it cannot answer from the available context rather than hallucinate. The response includes a confidence score.

**What happens with corrupt files?**
The parser catches extraction failures, marks the document as `FAILED`, and returns an error through the task status endpoint. The API never blocks.

---

## Limitations

- No formal retrieval evaluation benchmark endpoint yet (RAG quality is tested via integration flow and manual question sets)
- No built-in rate limiting (should be added for production)
- No circuit breaker for LLM provider outages
- File storage is local disk (not S3/blob storage)
- No document versioning or replacement endpoint

---

## Project Structure

```
src/app/
  api/           Routers, middleware, error handlers, UI routes
  services/      Ingestion, retrieval, QA, conversation orchestration
  processing/    PDF/DOCX parsers, text chunking
  vectorstore/   FAISS index + BM25 search + persistence
  llm/           LLM client abstraction + prompt templates
  db/            SQLAlchemy models + async session factory
  queue/         Celery app + ingestion task definitions
  core/          Config, logging, security
  schemas/       Pydantic request/response models

tests/           Unit + integration test suites
alembic/         Database migration scripts
postman/         Importable API collection + environment
sample_docs/     13 ready-to-upload test documents
```
