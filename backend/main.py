import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import get_db, init_db
from backend.llm_engine.client import llm_engine
from backend.models.schemas import APIResponse
from backend.routers.sessions import router as sessions_router

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("NeuroTune starting up")
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed")

    try:
        await llm_engine.load()
        logger.info("LLM engine loaded")
    except Exception:
        logger.exception("LLM load failed")

    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

app.include_router(sessions_router)


@app.get("/", response_model=APIResponse)
async def root():
    return APIResponse(
        success=True,
        message="API running",
        data={"version": settings.api_version, "description": settings.api_description},
    )


@app.get("/health", response_model=APIResponse)
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return APIResponse(
        success=True,
        message="API health check",
        data={"status": "healthy", "version": settings.api_version, "database": db_status},
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error": "Endpoint error",
            "details": f"Endpoint {request.url.path} doesn't exist",
        },
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error", "details": "Server errored"},
    )


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug",
    )
