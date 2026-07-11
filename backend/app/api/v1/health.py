from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["System"])


@router.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.app_env,
        "neshan_configured": bool(settings.neshan_api_key),
        "llm_configured": bool(settings.openai_api_key),
    }
