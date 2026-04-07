from __future__ import annotations

from fastapi import Request


def get_document_service(request: Request):
    return request.app.state.document_service


def get_conversation_service(request: Request):
    return request.app.state.conversation_service


def get_qa_service(request: Request):
    return request.app.state.qa_service


def get_celery_app(request: Request):
    return request.app.state.celery_app
