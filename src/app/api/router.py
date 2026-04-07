from fastapi import APIRouter, Depends

from app.api.v1 import conversations, documents, health, tasks
from app.core.security import verify_api_key

api_router = APIRouter(dependencies=[Depends(verify_api_key)])
api_router.include_router(health.router)
api_router.include_router(documents.router)
api_router.include_router(tasks.router)
api_router.include_router(conversations.router)
