from fastapi import APIRouter

from ..config import settings
from ..schemas import ConfigResponse, HealthResponse


router = APIRouter(prefix="/api")


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(ok=True)


@router.get("/config", response_model=ConfigResponse)
def get_config() -> ConfigResponse:
    return ConfigResponse(
        app_url=str(settings.app_url),
        web_url=settings.web_url,
        rag_enabled=settings.rag_enabled,
        llm_enabled=settings.llm_enabled,
        telegram_mode=settings.telegram_mode,
        reminder_hours_before=settings.reminder_hours_before,
        reminder_1_hours_before=settings.reminder_1_hours_before,
        reminder_2_hours_before=settings.reminder_2_hours_before,
    )


@router.get("/settings")
def get_settings() -> dict:
    return {
        "app_env": settings.app_env,
        "app_url": str(settings.app_url),
        "web_url": settings.web_url,
        "tz": settings.tz,
        "rag_enabled": settings.rag_enabled,
        "llm_enabled": settings.llm_enabled,
        "telegram_mode": settings.telegram_mode,
        "allowed_formats": settings.allowed_formats_list,
        "allowed_time_prefs": settings.allowed_time_prefs_list,
    }


@router.get("/analytics")
def get_analytics() -> dict:
    return {
        "ok": True,
        "summary": {
            "total_leads": 0,
            "total_bookings": 0,
            "conversion_rate": 0.0,
        },
    }

