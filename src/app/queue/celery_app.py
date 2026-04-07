from __future__ import annotations

from celery import Celery

from app.config import get_settings

celery_app = Celery("smart_doc_qa", include=["app.queue.celery_tasks"])


def configure_celery_app() -> Celery:
    settings = get_settings()
    celery_app.conf.update(
        broker_url=settings.celery_broker_url,
        result_backend=settings.celery_result_backend,
        task_track_started=True,
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        task_ignore_result=False,
        task_always_eager=settings.celery_task_always_eager,
        task_store_eager_result=settings.celery_task_store_eager_result,
    )
    return celery_app


configure_celery_app()
