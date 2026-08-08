"""Interview API route — single endpoint as per Technical Specification."""

from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.api.dependencies import get_interview_service
from app.services.interview_service import InterviewService

router = APIRouter()


# ─── Request/Response models matching the Technical Spec ──────────────────────


class InterviewRequest(BaseModel):
    """Single endpoint request — handles both start and conversation turns."""
    sessionId: str
    candidate: Optional[dict[str, Any]] = None  # Present on first call only
    message: Optional[str] = None  # Present on subsequent calls


class FeedbackPayload(BaseModel):
    summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    next: list[str] = Field(default_factory=list)


class InterviewResponse(BaseModel):
    """Response for all interview turns."""
    reply: str
    done: bool = False
    feedback: Optional[FeedbackPayload] = None


# ─── The single endpoint ──────────────────────────────────────────────────────


@router.post("/api/interview", response_model=InterviewResponse)
async def interview_endpoint(request: InterviewRequest):
    """Single interview endpoint as per Technical Specification.

    - First call: sessionId + candidate → starts interview
    - Subsequent calls: sessionId + message → conversation turn
    - Final response: done=true + feedback
    """
    service = get_interview_service()

    try:
        # Case 1: Start interview (candidate object present)
        if request.candidate is not None:
            candidate_id = request.candidate.get(
                "candidate_id", request.candidate.get("id", request.sessionId)
            )

            # Always load full candidate from candidates.json
            candidate_data = _load_candidate_by_id(candidate_id)
            if not candidate_data or candidate_data.get("name") == "":
                # Fallback: use whatever was sent in the request
                candidate_data = request.candidate
                candidate_data.setdefault("candidate_id", candidate_id)
                candidate_data.setdefault("name", candidate_id)

            result = await service.start_interview(
                candidate_id=candidate_id,
                session_id=request.sessionId,
                candidate_data=candidate_data,
            )
            return InterviewResponse(
                reply=result["message"],
                done=False,
            )

        # Case 2: Conversation turn (message present)
        elif request.message is not None:
            result = await service.submit_answer(
                interview_id=request.sessionId,
                answer=request.message,
            )

            # Case 3: Interview complete
            if result.get("is_complete", False):
                feedback_data = result.get("feedback", {})
                feedback = FeedbackPayload(
                    summary=feedback_data.get("summary", "Interview completed."),
                    strengths=[
                        s.get("area", "") + ": " + s.get("description", "")
                        for s in feedback_data.get("strengths", [])
                    ] if feedback_data.get("strengths") else [],
                    gaps=[
                        w.get("area", "") + ": " + w.get("description", "")
                        for w in feedback_data.get("weaknesses", [])
                    ] if feedback_data.get("weaknesses") else [],
                    next=[
                        f"Day {r.get('curriculum_day', '')}: {r.get('reason', '')}"
                        for r in feedback_data.get("recommendations", [])
                    ] if feedback_data.get("recommendations") else [],
                )
                return InterviewResponse(
                    reply=result["message"],
                    done=True,
                    feedback=feedback,
                )

            return InterviewResponse(
                reply=result["message"],
                done=False,
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Request must include either 'candidate' (to start) or 'message' (to respond)",
            )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _load_candidate_by_id(candidate_id: str) -> dict:
    """Load full candidate data from candidates.json by ID."""
    import json
    from pathlib import Path

    # Search multiple paths (local dev + Docker)
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
        return {"candidate_id": candidate_id, "name": "", "completed_missions": [], "skipped_topics": [], "learning_signals": [], "performance": {}, "projects": [], "tools_used": []}

    with open(candidates_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for c in data.get("candidates", []):
        member = c.get("member", {})
        if member.get("id") == candidate_id:
            missions = c.get("missions", [])
            signals = c.get("signals", {})
            return {
                "candidate_id": member.get("id"),
                "name": member.get("name", ""),
                "completed_missions": [
                    {
                        "day": m.get("day", 0),
                        "mission": m.get("title", ""),
                        "status": "completed" if m.get("passed") else ("skipped" if m.get("skipped") else "failed"),
                        "score": round(1.0 / max(m.get("attempts", 1), 1), 2) if m.get("passed") else 0.0,
                        "attempts": m.get("attempts", 1),
                    }
                    for m in missions
                ],
                "skipped_topics": [m.get("day") for m in missions if m.get("skipped")],
                "learning_signals": [],
                "performance": {
                    "commit_days": round(signals.get("commitDays", 0) / 31.0, 2),
                    "missions_completed": round(signals.get("missionsCompleted", 0) / 31.0, 2),
                    "first_try_rate": round(signals.get("missionsFirstTry", 0) / max(signals.get("missionsCompleted", 1), 1), 2),
                },
                "projects": [m.get("title") for m in missions if m.get("passed")],
                "tools_used": [],
            }

    # Not found — return minimal valid structure
    return {"candidate_id": candidate_id, "name": candidate_id, "completed_missions": [], "skipped_topics": [], "learning_signals": [], "performance": {}, "projects": [], "tools_used": []}
