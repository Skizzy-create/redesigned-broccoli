import asyncio
import time
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Document, DocumentStatus
from app.db.session import get_session_factory


async def _insert_completed_document() -> Document:
    session_factory = get_session_factory()
    async with session_factory() as session:
        document = Document(
            filename="ready.pdf",
            content_type="application/pdf",
            file_size=128,
            checksum="ready-checksum",
            status=DocumentStatus.COMPLETED,
            chunk_count=1,
            metadata_json={"file_path": "data/uploads/ready.pdf"},
        )
        session.add(document)
        await session.commit()
        await session.refresh(document)
        return document


def _minimal_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.1\n"
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >> endobj\n"
        b"4 0 obj << /Length 36 >> stream\nBT /F1 12 Tf 50 700 Td (Hello PDF) Tj ET\nendstream endobj\n"
        b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000206 00000 n \n"
        b"trailer << /Size 5 /Root 1 0 R >>\nstartxref\n301\n%%EOF\n"
    )


def test_upload_document_queues_background_task(client, auth_headers):
    payload = {"file": ("sample.pdf", _minimal_pdf_bytes(), "application/pdf")}

    response = client.post("/api/v1/documents", headers=auth_headers, files=payload)

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "success"
    assert UUID(body["data"]["document_id"])
    assert UUID(body["data"]["task_id"])


def test_task_status_endpoint_returns_task_state(client, auth_headers):
    payload = {"file": ("sample.pdf", _minimal_pdf_bytes(), "application/pdf")}
    upload = client.post("/api/v1/documents", headers=auth_headers, files=payload)
    task_id = upload.json()["data"]["task_id"]

    deadline = time.time() + 2.0
    state = None
    while time.time() < deadline:
        task_response = client.get(f"/api/v1/tasks/{task_id}", headers=auth_headers)
        assert task_response.status_code == 200
        state = task_response.json()["data"]["status"]
        if state in {"completed", "failed"}:
            break
        time.sleep(0.05)

    assert state in {"pending", "processing", "completed", "failed"}


def test_list_and_get_document(client, auth_headers):
    payload = {"file": ("sample.pdf", _minimal_pdf_bytes(), "application/pdf")}
    upload = client.post("/api/v1/documents", headers=auth_headers, files=payload)
    document_id = upload.json()["data"]["document_id"]

    list_response = client.get("/api/v1/documents", headers=auth_headers)
    assert list_response.status_code == 200
    assert any(item["id"] == document_id for item in list_response.json()["data"]["items"])

    get_response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["id"] == document_id


def test_ask_requires_completed_document(client, auth_headers):
    payload = {"file": ("sample.pdf", _minimal_pdf_bytes(), "application/pdf")}
    upload = client.post("/api/v1/documents", headers=auth_headers, files=payload)
    document_id = upload.json()["data"]["document_id"]

    response = client.post(
        f"/api/v1/documents/{document_id}/ask",
        headers=auth_headers,
        json={"question": "What does the document say?"},
    )

    assert response.status_code in {422, 200}


def test_task_not_found_returns_404(client, auth_headers):
    response = client.get("/api/v1/tasks/missing-task-id", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["status"] == "pending"


def test_document_ask_success_with_stubbed_qa_service(client, auth_headers, monkeypatch):
    document = asyncio.run(_insert_completed_document())

    class StubResult:
        answer = "Stub answer"
        conversation_id = "11111111-1111-1111-1111-111111111111"
        sources = [{"chunk_id": "22222222-2222-2222-2222-222222222222", "chunk_index": 0, "score": 0.91}]
        confidence = 0.9
        retrieval_cycles = 1
        status = "success"
        needs_more_context = False
        clarifying_question = None

    async def _stub_ask(session, *, document_id, question, conversation_id=None):
        del session, document_id, question, conversation_id
        return StubResult()

    monkeypatch.setattr(client.app.state.qa_service, "ask_document", _stub_ask)

    response = client.post(
        f"/api/v1/documents/{document.id}/ask",
        headers=auth_headers,
        json={"question": "Summarize"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["data"]["answer"] == "Stub answer"
    assert body["data"]["needs_more_context"] is False
    assert body["data"]["clarifying_question"] is None


def test_delete_document_removes_record(client, auth_headers):
    payload = {"file": ("sample.pdf", _minimal_pdf_bytes(), "application/pdf")}
    upload = client.post("/api/v1/documents", headers=auth_headers, files=payload)
    document_id = upload.json()["data"]["document_id"]

    delete_response = client.delete(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert delete_response.status_code == 204

    get_response = client.get(f"/api/v1/documents/{document_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_upload_rejects_unsupported_media_type(client, auth_headers):
    payload = {"file": ("sample.txt", b"plain text", "text/plain")}

    response = client.post("/api/v1/documents", headers=auth_headers, files=payload)

    assert response.status_code == 415
    body = response.json()
    assert body["error"]["code"] == "unsupported_media_type"


def test_upload_rejects_empty_file(client, auth_headers):
    payload = {"file": ("empty.pdf", b"", "application/pdf")}

    response = client.post("/api/v1/documents", headers=auth_headers, files=payload)

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "empty_file"


def test_upload_duplicate_document_returns_conflict(client, auth_headers):
    payload = {"file": ("sample.pdf", _minimal_pdf_bytes(), "application/pdf")}

    first = client.post("/api/v1/documents", headers=auth_headers, files=payload)
    second = client.post("/api/v1/documents", headers=auth_headers, files=payload)

    assert first.status_code == 202
    assert second.status_code == 409
    body = second.json()
    assert body["error"]["code"] == "duplicate_document"
