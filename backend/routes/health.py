import asyncio
import concurrent.futures
import threading
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.config import Settings, get_settings
from backend.database import get_db, check_db_health
from backend.schemas import HealthResponse, SystemInfoResponse, SystemServiceStatus
from backend.services.speech_service import speech_service
from backend.services.voice_service import voice_service

router = APIRouter(tags=["System & Health"])

# Dedicated bounded worker pool for non-blocking health checks
MAX_READINESS_WORKERS = 2
_health_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=MAX_READINESS_WORKERS,
    thread_name_prefix="warkari_health"
)
_readiness_semaphore = threading.BoundedSemaphore(value=MAX_READINESS_WORKERS)


def _bounded_check_db_health(timeout_seconds: float) -> bool:
    """Wrapper that releases the worker semaphore only after the actual DB operation finishes."""
    try:
        return check_db_health(timeout_seconds=timeout_seconds)
    finally:
        _readiness_semaphore.release()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint (Liveness probe)",
    description="Returns the immediate liveness status of the Warkari API process with zero I/O and zero database queries."
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")


@router.get(
    "/ready",
    summary="Readiness check endpoint (Readiness probe)",
    description="Verifies database accessibility with strict 3-second ceiling and bounded worker admission. Returns 200 if connected, 503 if unreachable or overloaded."
)
async def readiness_check():
    """Asynchronously bounded readiness probe with saturated worker protection.
    
    Guarantees:
    - Never blocks the asyncio event loop.
    - Rejects excess requests immediately with 503 if all readiness workers are occupied.
    - Zero unbounded queue accumulation in ThreadPoolExecutor.
    - Releases worker slot only when the underlying DB query/connection terminates.
    - Enforces a hard 3.0-second async deadline for the HTTP caller.
    """
    # 1. Non-blocking admission check: reject immediately if both workers are active
    slot_acquired = _readiness_semaphore.acquire(blocking=False)
    if not slot_acquired:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "busy"}
        )

    # 2. Slot acquired: submit to executor. The slot is released inside _bounded_check_db_health
    loop = asyncio.get_running_loop()
    try:
        try:
            fut = loop.run_in_executor(_health_executor, _bounded_check_db_health, 2.5)
        except Exception:
            _readiness_semaphore.release()
            raise
        is_ready = await asyncio.wait_for(asyncio.shield(fut), timeout=3.0)
    except (asyncio.TimeoutError, TimeoutError):
        is_ready = False
    except Exception:
        is_ready = False

    if is_ready:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "ready", "database": "connected"})
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "degraded", "database": "unreachable"}
    )





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


