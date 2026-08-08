"""AI Interview Agent — FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from app.api.routes import health, interview
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.candidate_service import CandidateService
from app.services.curriculum_service import CurriculumService

# Resolve frontend dist directory
STATIC_DIR = Path(__file__).parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management."""
    setup_logging()
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
        description="Production-grade AI-powered technical interviewer",
        version="1.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Routes (registered FIRST so they take priority)
    app.include_router(health.router)
    app.include_router(interview.router)

    # Serve frontend static assets if dist exists
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        # Mount static assets (JS, CSS, images)
        assets_dir = STATIC_DIR / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="static-assets")

        # Catch-all: serve index.html for SPA routing
        @app.get("/{full_path:path}")
        async def serve_spa(request: Request, full_path: str):
            """Serve the React SPA for any non-API path."""
            # Don't intercept API or health paths
            if full_path.startswith("api/") or full_path in ("health", "docs", "openapi.json"):
                return JSONResponse({"error": "Not found"}, status_code=404)

            # Try serving the exact file
            file_path = STATIC_DIR / full_path
            if full_path and file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))

            # Default: serve index.html (SPA client-side routing)
            return FileResponse(str(STATIC_DIR / "index.html"))

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
