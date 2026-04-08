import asyncio
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from app.main import create_app
from app.config import get_settings
from app.db.base import Base
from app.db.session import clear_session_caches, get_engine


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    clear_session_caches()
    yield
    get_settings.cache_clear()
    clear_session_caches()


@pytest.fixture
def app(monkeypatch):
    db_path = Path(f"test_app_{uuid4().hex}.db")
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("CELERY_BROKER_URL", "memory://")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "cache+memory://")
    monkeypatch.setenv("CELERY_TASK_ALWAYS_EAGER", "false")
    monkeypatch.setenv("CELERY_TASK_STORE_EAGER_RESULT", "false")

    async def _prepare_db() -> None:
        engine = get_engine()
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(_prepare_db())
    application = create_app()
    yield application

    async def _cleanup_db() -> None:
        engine = get_engine()
        await engine.dispose()

    asyncio.run(_cleanup_db())
    clear_session_caches()
    if db_path.exists():
        try:
            db_path.unlink(missing_ok=True)
        except PermissionError:
            pass


@pytest.fixture
def client(app):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers():
    return {"X-API-Key": get_settings().api_key}
