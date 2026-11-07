from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.config import Settings, get_settings
from backend.database import get_db
from backend.schemas import HealthResponse, SystemInfoResponse, SystemServiceStatus
from backend.services.speech_service import speech_service
from backend.services.voice_service import voice_service

router = APIRouter(tags=["System & Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
    description="Returns the basic liveness/health status of the Warkari API service."
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@router.get(
    "/api/system/info",
    response_model=SystemInfoResponse,
    summary="System and service operational information",
    description="Returns application version and configuration status of connected services without exposing secrets."
)
async def get_system_info(
    settings: Settings = Depends(get_settings),
    db: Session = Depends(get_db)
) -> SystemInfoResponse:
    # Verify Database connectivity
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:
        db_status = f"unhealthy: {str(exc)}"

    stt_status = "configured" if speech_service.is_configured else "unconfigured (missing API key)"
    tts_status = "configured" if voice_service.is_configured else "unconfigured (missing API key)"

    return SystemInfoResponse(
        project=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        status="operational",
        services=SystemServiceStatus(
            database=db_status,
            gnani_stt_service=stt_status,
            gnani_tts_service=tts_status
        )
    )

