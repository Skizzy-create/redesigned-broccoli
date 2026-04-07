from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI

from app.api.error_handlers import register_error_handlers
from app.api.middleware import RequestContextMiddleware
from app.api.router import api_router
from app.api.ui_router import ui_router
from app.config import get_settings
from app.core.logging import configure_logging
from app.embeddings.encoder import CrossEncoderReranker, EmbeddingEncoder
from app.llm.provider import LLMProvider
from app.queue.celery_app import configure_celery_app
from app.services.conversation_service import ConversationService
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService
from app.services.qa_service import QAService
from app.services.retrieval_service import RetrievalService
from app.vectorstore.faiss_store import FaissStore


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.index_dir).mkdir(parents=True, exist_ok=True)

    encoder = EmbeddingEncoder(settings.embedding_model)
    reranker = CrossEncoderReranker(settings.reranker_model)
    faiss_store = FaissStore(settings.index_dir)
    celery_app = configure_celery_app()

    ingestion_service = IngestionService(encoder=encoder, faiss_store=faiss_store)
    retrieval_service = RetrievalService(encoder=encoder, reranker=reranker, faiss_store=faiss_store)
    conversation_service = ConversationService()
    llm_provider = LLMProvider()
    qa_service = QAService(
        retrieval_service=retrieval_service,
        conversation_service=conversation_service,
        llm_provider=llm_provider,
    )
    document_service = DocumentService(faiss_store=faiss_store)

    app.state.celery_app = celery_app
    app.state.document_service = document_service
    app.state.ingestion_service = ingestion_service
    app.state.retrieval_service = retrieval_service
    app.state.conversation_service = conversation_service
    app.state.qa_service = qa_service
    app.state.is_ready = True
    yield
    app.state.is_ready = False


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Upload documents and ask grounded questions using RAG.",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.include_router(ui_router)
    app.include_router(api_router, prefix=settings.api_v1_prefix)
    register_error_handlers(app)
    return app


app = create_app()
