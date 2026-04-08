# Test Coverage and Quality Assurance

## Purpose

This document defines the project's enterprise-quality testing standards, what is currently covered, and which controls must pass before release.

## Quality Policy

The service follows a quality-first policy:

1. No endpoint change ships without automated coverage updates.
2. Every defect gets a regression test.
3. API contract compatibility is verified before merge.
4. Runtime behavior is validated in Docker, not only local development.
5. Production readiness requires green quality gates.

## Enterprise Quality Gates

A change is considered release-ready only when all gates are green:

1. Static quality gate
- Python diagnostics show no new errors in changed files.
- API schema remains valid and loadable.

2. Unit and integration gate
- Full pytest suite passes.
- No failing test can be ignored.

3. Container gate
- docker compose config resolves successfully.
- All services become healthy: app, db, redis, worker.

4. API smoke gate
- Health endpoint returns healthy database state.
- Upload, task polling, and conversational flow execute successfully.

5. Contract gate
- Postman collection covers all documented public API routes.
- Environment variables in Postman align with deployment defaults.

## Current Automated Test Inventory

Current tests are organized as follows:

- Unit tests
  - Configuration defaults and environment overrides.
  - Enum stability and queue model behavior.
  - QA service edge behavior:
    - Document missing and not-ready validation.
    - Multi-cycle retrieval when confidence is low.
    - `needs_more_context` clarification response path.
    - LLM failure fallback response path.

- Integration tests
  - Health and readiness endpoints.
  - Document upload/list/get/ask/delete flows.
  - Document upload edge cases:
    - Unsupported media type.
    - Empty file rejection.
    - Duplicate checksum conflict.
  - Task status endpoint behavior.
  - Conversation list/get/follow-up/delete flows.
  - Data model constraints and cascade behavior.
  - UI route availability.

## API Coverage Matrix

| Area | Route Pattern | Automated Coverage |
|---|---|---|
| Health | /api/v1/health, /api/v1/health/ready | Covered |
| Documents | /api/v1/documents (POST/GET), /api/v1/documents/{id} (GET/DELETE), /api/v1/documents/{id}/ask (POST) | Covered |
| Tasks | /api/v1/tasks/{task_id} (GET) | Covered |
| Conversations | /api/v1/conversations (GET), /api/v1/conversations/{id} (GET/DELETE), /api/v1/conversations/{id}/ask (POST) | Covered |
| UI | /ui, /ui/docs, /favicon.ico | Covered |

## Docker Validation Baseline

The baseline validation for each release is:

1. Build and run with Docker Compose.
2. Confirm healthy service status for db and redis plus started state for app and worker.
3. Execute API smoke sequence:
- Health check
- Upload a sample PDF/DOCX
- Poll task status to completed
- Ask question
- Ask follow-up

## Postman Contract Audit

The collection at postman/Smart-Document-QA.postman_collection.json is audited against implemented routes in src/app/api/v1.

Audit summary:

- Health and readiness: covered
- Document CRUD and ask: covered
- Task status polling: covered
- Conversation CRUD and follow-up: covered
- Optional UI request: covered

Environment alignment requirements:

- baseUrl points to /api/v1
- apiKey must match deployment API_KEY
- sample file paths are valid for local collection runs

## Known Observations

1. First ingestion after fresh startup can be slower due to sentence-transformers model download.
2. If OpenAI key is placeholder-only, ask endpoints still return partial responses from retrieval fallback logic.
3. When retrieval confidence is insufficient, API returns `needs_more_context` with a clarifying question instead of guessing.
4. Docker first build is significantly slower than subsequent builds due dependency download and image-layer warm-up.

## Operational Recommendations

1. Use real OPENAI_API_KEY in production-like validation.
2. Keep a nightly Docker smoke test that executes the full upload-to-conversation flow.
3. Track endpoint latency and task completion times for regression detection.
4. Add coverage.py reporting if percentage gating is needed by policy.
