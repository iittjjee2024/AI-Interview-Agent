"""Health check and candidates endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.domain.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/api/candidates")
async def get_candidates():
    """Return all available candidates for the frontend."""
    import json
    from pathlib import Path

    # Try multiple paths (handles both local dev and Docker)
    base = Path(__file__).parent.parent.parent.parent  # project root
    candidates_path = None
    for p in [
        base / "candidates.json",
        Path("candidates.json"),
        Path("data/candidates.json"),
        base / "data" / "candidates.json",
    ]:
        if p.exists():
            candidates_path = p
            break

    if not candidates_path:
        return {"candidates": []}

    with open(candidates_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Format for frontend display
    candidates = []
    for c in data.get("candidates", []):
        member = c.get("member", {})
        signals = c.get("signals", {})
        candidates.append({
            "id": member.get("id", ""),
            "name": member.get("name", "Unknown"),
            "jobRole": member.get("jobRole", ""),
            "yearsExperience": member.get("yearsExperience", 0),
            "missionsCompleted": signals.get("missionsCompleted", 0),
            "commitDays": signals.get("commitDays", 0),
        })

    return {"candidates": candidates}
