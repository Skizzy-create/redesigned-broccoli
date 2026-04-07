from __future__ import annotations

from fastapi import APIRouter
from fastapi import Response
from fastapi.responses import HTMLResponse

ui_router = APIRouter()


_UI_HTML = """
<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Smart Document QA Console</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

    :root {
      --bg: #f2efe8;
      --card: #fffaf0;
      --ink: #1d2b34;
      --muted: #5c6970;
      --accent: #0f766e;
      --accent-2: #e07a2a;
      --ok: #0f9d58;
      --warn: #b45309;
      --danger: #b42318;
      --border: #d8d2c6;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      font-family: 'Space Grotesk', sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at 8% 12%, #f8d8b2 0, transparent 28%),
        radial-gradient(circle at 90% 18%, #bdddd7 0, transparent 32%),
        linear-gradient(160deg, #f3f1ec 0%, #ece8dd 100%);
      min-height: 100vh;
      padding: 20px;
    }

    .shell {
      max-width: 1100px;
      margin: 0 auto;
      display: grid;
      gap: 16px;
    }

    .hero {
      background: linear-gradient(135deg, rgba(15, 118, 110, 0.16), rgba(224, 122, 42, 0.14));
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 6px 20px rgba(0, 0, 0, 0.07);
      animation: rise 380ms ease-out;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(1.6rem, 2.6vw, 2.3rem);
      letter-spacing: 0.01em;
    }

    .hero p {
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.45;
    }

    .hero-nav {
      margin-top: 12px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .hero-nav a {
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 999px;
      border: 1px solid var(--border);
      background: #fff;
      color: var(--ink);
      padding: 6px 12px;
      font-size: 0.8rem;
      font-weight: 600;
      transition: transform 120ms ease, box-shadow 120ms ease;
    }

    .hero-nav a:hover {
      transform: translateY(-1px);
      box-shadow: 0 3px 10px rgba(0, 0, 0, 0.1);
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      gap: 14px;
    }

    .card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 14px;
      box-shadow: 0 4px 14px rgba(18, 23, 29, 0.06);
      animation: rise 420ms ease-out;
    }

    .card h2 {
      margin: 0 0 10px;
      font-size: 1.06rem;
    }

    label {
      display: block;
      font-size: 0.86rem;
      color: var(--muted);
      margin: 8px 0 4px;
    }

    input, textarea, button {
      width: 100%;
      border-radius: 10px;
      border: 1px solid var(--border);
      padding: 9px 10px;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.86rem;
      color: var(--ink);
      background: #fff;
    }

    textarea {
      min-height: 82px;
      resize: vertical;
    }

    button {
      margin-top: 10px;
      cursor: pointer;
      border-color: transparent;
      background: linear-gradient(135deg, var(--accent), #1f8f84);
      color: #fff;
      font-weight: 600;
      transition: transform 120ms ease, filter 120ms ease;
    }

    button.alt {
      background: linear-gradient(135deg, var(--accent-2), #e99b4e);
    }

    button:active {
      transform: translateY(1px);
    }

    .status {
      padding: 10px 12px;
      border-radius: 10px;
      font-size: 0.84rem;
      border: 1px solid var(--border);
      background: #fff;
      font-family: 'IBM Plex Mono', monospace;
      min-height: 39px;
    }

    .status.ok {
      border-color: rgba(15, 157, 88, 0.35);
      color: var(--ok);
    }

    .status.warn {
      border-color: rgba(180, 83, 9, 0.35);
      color: var(--warn);
    }

    .status.err {
      border-color: rgba(180, 35, 24, 0.35);
      color: var(--danger);
    }

    .console {
      background: #111827;
      color: #e5e7eb;
      border-radius: 14px;
      border: 1px solid #2b3343;
      padding: 10px;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.02);
    }

    .console h2 {
      margin: 0 0 8px;
      font-size: 1rem;
      color: #f9fafb;
    }

    pre {
      margin: 0;
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.8rem;
      white-space: pre-wrap;
      max-height: 420px;
      overflow: auto;
      line-height: 1.45;
    }

    @keyframes rise {
      from {
        opacity: 0;
        transform: translateY(8px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
  </style>
</head>
<body>
  <main class=\"shell\">
    <section class=\"hero\">
      <h1>Smart Document QA Console</h1>
      <p>
        This page is optional and intended for easier manual testing. The API server is the primary interface and remains fully active for all integrations.
      </p>
      <div class="hero-nav">
        <a href="/docs">Open Swagger</a>
        <a href="/ui/docs">Open Component Docs</a>
      </div>
    </section>

    <section class=\"grid\">
      <article class=\"card\">
        <h2>Connection</h2>
        <label for=\"apiBase\">API Base</label>
        <input id=\"apiBase\" type=\"text\" value=\"/api/v1\" />

        <label for=\"apiKey\">X-API-Key</label>
        <input id=\"apiKey\" type=\"text\" value=\"dev-api-key\" />

        <button id=\"healthBtn\">Check Health</button>
        <div id=\"healthStatus\" class=\"status\">Idle.</div>
      </article>

      <article class=\"card\">
        <h2>Upload Document</h2>
        <label for=\"uploadFile\">PDF or DOCX</label>
        <input id=\"uploadFile\" type=\"file\" accept=\".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document\" />
        <button id=\"uploadBtn\">Upload and Queue</button>
      </article>

      <article class=\"card\">
        <h2>Task Status</h2>
        <label for=\"taskId\">Task ID</label>
        <input id=\"taskId\" type=\"text\" placeholder=\"paste task id\" />
        <button id=\"taskBtn\" class=\"alt\">Check Task</button>
      </article>

      <article class=\"card\">
        <h2>Documents</h2>
        <button id=\"listDocsBtn\" class=\"alt\">List Documents</button>

        <label for=\"documentId\">Document ID</label>
        <input id=\"documentId\" type=\"text\" placeholder=\"document id\" />

        <label for=\"conversationId\">Conversation ID (optional)</label>
        <input id=\"conversationId\" type=\"text\" placeholder=\"conversation id\" />
      </article>

      <article class=\"card\" style=\"grid-column: 1 / -1;\">
        <h2>Ask Question</h2>
        <label for=\"question\">Question</label>
        <textarea id=\"question\" placeholder=\"Ask grounded questions about your document\"></textarea>
        <button id=\"askBtn\">Ask</button>
      </article>
    </section>

    <section class=\"console\">
      <h2>API Response Console</h2>
      <pre id=\"output\">Ready.</pre>
    </section>
  </main>

  <script>
    const output = document.getElementById('output');
    const healthStatus = document.getElementById('healthStatus');

    function baseUrl() {
      const value = document.getElementById('apiBase').value.trim();
      return value.endsWith('/') ? value.slice(0, -1) : value;
    }

    function apiKey() {
      return document.getElementById('apiKey').value.trim();
    }

    function setOutput(label, payload) {
      const block = typeof payload === 'string' ? payload : JSON.stringify(payload, null, 2);
      output.textContent = label + '\\n\\n' + block;
    }

    async function apiFetch(path, options) {
      const headers = options && options.headers ? options.headers : {};
      headers['X-API-Key'] = apiKey();
      const response = await fetch(baseUrl() + path, {
        method: options && options.method ? options.method : 'GET',
        headers,
        body: options && options.body ? options.body : undefined,
      });

      const text = await response.text();
      let data = text;
      try {
        data = JSON.parse(text);
      } catch (e) {
      }

      return { ok: response.ok, status: response.status, data };
    }

    document.getElementById('healthBtn').addEventListener('click', async () => {
      const result = await apiFetch('/health', {});
      setOutput('Health Check', result);
      healthStatus.textContent = 'HTTP ' + result.status;
      healthStatus.className = 'status ' + (result.ok ? 'ok' : 'err');
    });

    document.getElementById('uploadBtn').addEventListener('click', async () => {
      const fileInput = document.getElementById('uploadFile');
      if (!fileInput.files || fileInput.files.length === 0) {
        setOutput('Upload', 'Please choose a file first.');
        return;
      }

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      const result = await apiFetch('/documents', {
        method: 'POST',
        body: formData,
      });
      setOutput('Upload', result);

      if (result.ok && result.data && result.data.data) {
        if (result.data.data.document_id) {
          document.getElementById('documentId').value = result.data.data.document_id;
        }
        if (result.data.data.task_id) {
          document.getElementById('taskId').value = result.data.data.task_id;
        }
      }
    });

    document.getElementById('taskBtn').addEventListener('click', async () => {
      const taskId = document.getElementById('taskId').value.trim();
      if (!taskId) {
        setOutput('Task', 'Provide a task id.');
        return;
      }
      const result = await apiFetch('/tasks/' + encodeURIComponent(taskId), {});
      setOutput('Task Status', result);
    });

    document.getElementById('listDocsBtn').addEventListener('click', async () => {
      const result = await apiFetch('/documents', {});
      setOutput('Documents', result);
      if (result.ok && result.data && result.data.data && Array.isArray(result.data.data.items) && result.data.data.items.length > 0) {
        document.getElementById('documentId').value = result.data.data.items[0].id;
      }
    });

    document.getElementById('askBtn').addEventListener('click', async () => {
      const documentId = document.getElementById('documentId').value.trim();
      const conversationId = document.getElementById('conversationId').value.trim();
      const question = document.getElementById('question').value.trim();

      if (!documentId) {
        setOutput('Ask', 'Provide a document id first.');
        return;
      }

      if (!question) {
        setOutput('Ask', 'Question cannot be empty.');
        return;
      }

      const path = conversationId
        ? '/conversations/' + encodeURIComponent(conversationId) + '/ask'
        : '/documents/' + encodeURIComponent(documentId) + '/ask';

      const result = await apiFetch(path, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ question })
      });

      setOutput('Ask', result);

      if (result.ok && result.data && result.data.data && result.data.data.conversation_id) {
        document.getElementById('conversationId').value = result.data.data.conversation_id;
      }
    });
  </script>
</body>
</html>
"""


_DOCS_HTML = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Smart Document QA - Component Docs</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap');

    :root {
      --ink: #1d2b34;
      --muted: #5c6970;
      --accent: #0f766e;
      --accent-soft: #d9f2ee;
      --warn-soft: #fce8d5;
      --panel: #fffdf7;
      --line: #d7d0c5;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      color: var(--ink);
      font-family: 'Space Grotesk', sans-serif;
      background:
        radial-gradient(circle at 15% 15%, #f7dfbf 0, transparent 26%),
        radial-gradient(circle at 88% 10%, #cde7e3 0, transparent 28%),
        linear-gradient(180deg, #f4f1e9 0%, #ece8de 100%);
      min-height: 100vh;
      padding: 22px;
    }

    .shell {
      max-width: 1160px;
      margin: 0 auto;
      display: grid;
      gap: 14px;
    }

    .hero {
      background: linear-gradient(135deg, rgba(15, 118, 110, 0.16), rgba(224, 122, 42, 0.12));
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(1.4rem, 2.2vw, 2.2rem);
    }

    .hero p {
      margin: 8px 0 0;
      color: var(--muted);
      line-height: 1.45;
    }

    .nav {
      margin-top: 12px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .nav a {
      text-decoration: none;
      border-radius: 999px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      padding: 6px 12px;
      font-size: 0.82rem;
      font-weight: 600;
    }

    .notice {
      border-left: 4px solid var(--accent);
      background: var(--accent-soft);
      border-radius: 10px;
      padding: 10px 12px;
      font-size: 0.9rem;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }

    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 12px;
    }

    .card h2 {
      margin: 0;
      font-size: 1rem;
    }

    .label {
      display: inline-block;
      margin-top: 8px;
      border-radius: 999px;
      background: var(--warn-soft);
      border: 1px solid #efcfa9;
      padding: 3px 8px;
      font-size: 0.75rem;
      font-family: 'IBM Plex Mono', monospace;
    }

    .list {
      margin: 8px 0 0;
      padding-left: 16px;
      color: var(--muted);
      line-height: 1.4;
      font-size: 0.9rem;
    }

    .mono {
      font-family: 'IBM Plex Mono', monospace;
      font-size: 0.82rem;
    }
  </style>
</head>
<body>
  <main class="shell">
    <section class="hero">
      <h1>Smart Document QA - Component Documentation</h1>
      <p>
        This page explains what goes where and how to use each major part of the system.
      </p>
      <div class="nav">
        <a href="/ui">Open Testing Console</a>
        <a href="/docs">Open Swagger Docs</a>
      </div>
    </section>

    <section class="notice">
      API-first design: the official integration surface is the API under <span class="mono">/api/v1</span>. The UI pages are optional helpers for faster manual testing and onboarding.
    </section>

    <section class="grid">
      <article class="card">
        <h2>API Layer</h2>
        <span class="label">Where: src/app/api</span>
        <ul class="list">
          <li>Versioned route definitions and request validation.</li>
          <li>Security via <span class="mono">X-API-Key</span>.</li>
          <li>Consistent response and error envelope.</li>
          <li>How to use: call endpoints via Swagger, Postman, or client SDKs.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Service Layer</h2>
        <span class="label">Where: src/app/services</span>
        <ul class="list">
          <li>Business logic for document lifecycle, ingestion, retrieval, QA, and conversations.</li>
          <li>Keeps routers thin and focused on HTTP concerns.</li>
          <li>How to use: extend existing services for new capabilities before touching route handlers.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Document Processing</h2>
        <span class="label">Where: src/app/processing</span>
        <ul class="list">
          <li>Parsers for PDF and DOCX extraction.</li>
          <li>Chunking strategy with overlap and token-aware boundaries.</li>
          <li>How to use: upload document, then poll task endpoint until processing is complete.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Retrieval Stack</h2>
        <span class="label">Where: src/app/embeddings + src/app/vectorstore</span>
        <ul class="list">
          <li>Sentence-transformer embeddings for semantic retrieval.</li>
          <li>FAISS index + BM25 lexical search.</li>
          <li>Cross-encoder reranker for final relevance ordering.</li>
          <li>How to use: ask endpoints automatically invoke this pipeline.</li>
        </ul>
      </article>

      <article class="card">
        <h2>LLM Provider</h2>
        <span class="label">Where: src/app/llm</span>
        <ul class="list">
          <li>OpenAI-compatible client wrapper for OpenAI/Gemini.</li>
          <li>Prompt templates for grounded responses.</li>
          <li>Fallback behavior when LLM is unavailable.</li>
          <li>How to use: configure provider keys in environment variables.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Queue and Background Workers</h2>
        <span class="label">Where: src/app/queue</span>
        <ul class="list">
          <li>In-memory task queue and worker pool.</li>
          <li>Tracks progress, completion, and failure state for uploads.</li>
          <li>How to use: read <span class="mono">task_id</span> from upload response and poll <span class="mono">/api/v1/tasks/{id}</span>.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Persistence Layer</h2>
        <span class="label">Where: src/app/db + alembic</span>
        <ul class="list">
          <li>SQLAlchemy async models for documents, chunks, conversations, and messages.</li>
          <li>Alembic migrations for schema lifecycle.</li>
          <li>How to use: compose startup auto-runs migrations.</li>
        </ul>
      </article>

      <article class="card">
        <h2>Testing and Tooling</h2>
        <span class="label">Where: tests + postman + /ui</span>
        <ul class="list">
          <li>Automated tests validate routes and service behavior.</li>
          <li>Importable Postman collection/environment for quick API validation.</li>
          <li>Optional UI for manual route checks without writing scripts.</li>
        </ul>
      </article>
    </section>
  </main>
</body>
</html>
"""


@ui_router.get("/ui", include_in_schema=False)
async def testing_ui() -> HTMLResponse:
    return HTMLResponse(content=_UI_HTML)


@ui_router.get("/ui/docs", include_in_schema=False)
async def ui_docs() -> HTMLResponse:
  return HTMLResponse(content=_DOCS_HTML)


@ui_router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)
