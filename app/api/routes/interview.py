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
            candidate_id = request.candidate.get("candidate_id", request.sessionId)
            result = await service.start_interview(
                candidate_id=candidate_id,
                session_id=request.sessionId,
                candidate_data=request.candidate,
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
