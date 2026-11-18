from fastapi import APIRouter

from app.api.v1.endpoints.auth import organizations
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.intelligence import ai_router, query_router
from app.api.v1.endpoints.intelligence import router as intelligence_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(organizations)
api_router.include_router(intelligence_router)
api_router.include_router(ai_router)
api_router.include_router(query_router)
