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
        telegram_mode=settings.telegram_mode,
        reminder_hours_before=settings.reminder_hours_before,
        reminder_1_hours_before=settings.reminder_1_hours_before,
        reminder_2_hours_before=settings.reminder_2_hours_before,
    )

