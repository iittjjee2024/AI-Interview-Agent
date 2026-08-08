"""AI Interview Agent — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, interview
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.candidate_service import CandidateService
from app.services.curriculum_service import CurriculumService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    setup_logging()
    # Pre-load curriculum and candidates
    curriculum_service = CurriculumService()
    candidate_service = CandidateService()
    await curriculum_service.load()
    await candidate_service.load()
    yield


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="AI Interview Agent",
        description="Production-grade AI-powered technical interviewer for the 31-day AI Engineering Cohort",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router)
    app.include_router(interview.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
    )
