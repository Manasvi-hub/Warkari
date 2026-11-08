"""Warkari Backend Application Entrypoint.

FastAPI REST API supporting the Warkari voice-first pilgrimage assistance platform.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import get_settings
from backend.database import init_db
from backend.routes.assistant import router as assistant_router
from backend.routes.health import router as health_router
from backend.routes.intelligence import router as intelligence_router
from backend.routes.auth import router as auth_router
from backend.routes.incident_workflow import router as incident_workflow_router
from backend.schemas import RootResponse

logger = logging.getLogger("warkari.startup")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager handling application startup and graceful shutdown."""
    # In production, tables are pre-migrated. Attempt schema validation safely
    try:
        init_db()
    except Exception as exc:
        logger.error("Database initialization check failed during startup: %s", exc)
    yield
    # Shutdown: Clean up resources if necessary


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred while processing the request.",
            "detail": str(exc) if settings.DEBUG else None
        }
    )


# Root Endpoint
@app.get(
    "/",
    response_model=RootResponse,
    summary="API Root Information",
    description="Returns welcome information and operational status of the Warkari platform."
)
async def root() -> RootResponse:
    return RootResponse(
        project="Warkari",
        message="Welcome to Warkari API",
        status="running"
    )


# Register Routers
app.include_router(health_router)
app.include_router(assistant_router)
app.include_router(intelligence_router)
app.include_router(auth_router)
app.include_router(incident_workflow_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
