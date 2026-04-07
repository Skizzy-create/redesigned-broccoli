from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

from app.config import get_settings
from app.db.session import get_engine
from app.schemas.common import Meta, SuccessResponse

router = APIRouter(prefix="/health", tags=["System"])


class HealthData(BaseModel):
    service: str
    version: str
    environment: str
    healthy: bool
    database: str


class ReadinessData(BaseModel):
    ready: bool


def _meta_from_request(request: Request) -> Meta:
    request_id = getattr(request.state, "request_id", "unknown")
    return Meta(request_id=request_id)


@router.get("", response_model=SuccessResponse[HealthData])
async def health_check(request: Request) -> SuccessResponse[HealthData]:
    settings = get_settings()
    db_status = "down"
    try:
        engine = get_engine()
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        db_status = "down"

    data = HealthData(
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        healthy=db_status == "up",
        database=db_status,
    )
    return SuccessResponse(data=data, meta=_meta_from_request(request))


@router.get("/ready", response_model=SuccessResponse[ReadinessData])
async def readiness_check(request: Request) -> SuccessResponse[ReadinessData]:
    is_ready = bool(getattr(request.app.state, "is_ready", False))
    data = ReadinessData(ready=is_ready)
    return SuccessResponse(data=data, meta=_meta_from_request(request))
