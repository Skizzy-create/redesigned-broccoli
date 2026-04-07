from __future__ import annotations

from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.exceptions import (
    ConflictError,
    PayloadTooLargeError,
    ServiceUnavailableError,
    UnsupportedMediaTypeError,
    ValidationError,
)
from app.db.models import DocumentStatus
from app.db.session import get_async_session
from app.dependencies import get_document_service, get_qa_service
from app.processing.parsers.factory import DocumentParserFactory
from app.queue.celery_tasks import ingest_document_task
from app.schemas.common import Meta, SuccessResponse
from app.schemas.documents import DocumentData, DocumentListData, DocumentUploadData
from app.schemas.questions import AskRequest, AskResponseData

router = APIRouter(prefix="/documents", tags=["Documents"])


def _meta(request: Request) -> Meta:
    return Meta(request_id=getattr(request.state, "request_id", "unknown"))


def _to_document_data(document) -> DocumentData:
    return DocumentData(
        id=str(document.id),
        filename=document.filename,
        content_type=document.content_type,
        file_size=document.file_size,
        status=document.status.value,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at,
        processed_at=document.processed_at,
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=SuccessResponse[DocumentUploadData])
async def upload_document(
    request: Request,
    file: UploadFile,
    session: AsyncSession = Depends(get_async_session),
    document_service=Depends(get_document_service),
) -> SuccessResponse[DocumentUploadData]:
    settings = get_settings()
    content_type = (file.content_type or "").lower().strip()
    filename = file.filename or "uploaded_document"

    parser_allowed_types = DocumentParserFactory.allowed_content_types()
    if content_type not in parser_allowed_types and Path(filename).suffix.lower() not in {".pdf", ".docx"}:
        raise UnsupportedMediaTypeError("Only PDF and DOCX uploads are supported.")

    content = await file.read()
    if not content:
        raise ValidationError("Uploaded file is empty.", code="empty_file")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise PayloadTooLargeError(
            f"File exceeds max upload size of {settings.max_upload_size_mb} MB.",
        )

    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_name = f"{uuid4()}_{Path(filename).name}"
    file_path = upload_dir / file_name
    file_path.write_bytes(content)

    checksum = document_service.checksum_from_bytes(content)
    try:
        document = await document_service.create_document(
            session,
            filename=filename,
            content_type=content_type,
            file_size=len(content),
            checksum=checksum,
            file_path=str(file_path),
        )
    except ConflictError:
        file_path.unlink(missing_ok=True)
        raise

    try:
        task_result = ingest_document_task.delay(str(document.id), str(file_path), content_type)
    except Exception as exc:
        document.status = DocumentStatus.FAILED
        document.error_message = "Failed to queue ingestion task."
        await session.commit()
        raise ServiceUnavailableError(
            "Background task broker is unavailable. Please retry shortly.",
            code="task_broker_unavailable",
        ) from exc

    payload = DocumentUploadData(
        document_id=str(document.id),
        task_id=task_result.id,
        message="Document queued for processing.",
    )
    return SuccessResponse(data=payload, meta=_meta(request))


@router.get("", response_model=SuccessResponse[DocumentListData])
async def list_documents(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    document_service=Depends(get_document_service),
) -> SuccessResponse[DocumentListData]:
    documents = await document_service.list_documents(session)
    return SuccessResponse(data=DocumentListData(items=[_to_document_data(item) for item in documents]), meta=_meta(request))


@router.get("/{document_id}", response_model=SuccessResponse[DocumentData])
async def get_document(
    request: Request,
    document_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    document_service=Depends(get_document_service),
) -> SuccessResponse[DocumentData]:
    document = await document_service.get_document(session, document_id)
    return SuccessResponse(data=_to_document_data(document), meta=_meta(request))


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    session: AsyncSession = Depends(get_async_session),
    document_service=Depends(get_document_service),
):
    await document_service.delete_document(session, document_id)
    return None


@router.post("/{document_id}/ask", response_model=SuccessResponse[AskResponseData])
async def ask_document(
    request: Request,
    document_id: UUID,
    body: AskRequest,
    session: AsyncSession = Depends(get_async_session),
    qa_service=Depends(get_qa_service),
) -> SuccessResponse[AskResponseData]:
    result = await qa_service.ask_document(
        session,
        document_id=document_id,
        question=body.question,
        conversation_id=None,
    )
    response = AskResponseData(
        answer=result.answer,
        conversation_id=str(result.conversation_id),
        sources=result.sources,
        confidence=result.confidence,
        retrieval_cycles=result.retrieval_cycles,
        status=result.status,
        needs_more_context=getattr(result, "needs_more_context", False),
        clarifying_question=getattr(result, "clarifying_question", None),
    )
    return SuccessResponse(data=response, meta=_meta(request))
