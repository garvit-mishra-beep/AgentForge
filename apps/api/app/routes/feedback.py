"""Finding-feedback routes — capture accept/reject for the quality flywheel."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from app.auth import require_user
from app.feedback_service import feedback_stats, record_feedback
from models.agent_outputs import Finding, Severity

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _db(request: Request):
    return request.app.state.db


class FeedbackCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    decision: str = Field(..., pattern="^(accepted|rejected)$")
    severity: str = "medium"
    file: str | None = None
    project_id: str | None = None
    task_id: str | None = None


@router.post("", status_code=201)
async def submit_feedback(
    body: FeedbackCreate,
    request: Request,
    user_id: str = Depends(require_user),
):
    db = _db(request)
    fingerprint = Finding(title=body.title, file=body.file, severity=Severity(body.severity)).fingerprint()
    await record_feedback(
        db,
        user_id=user_id,
        fingerprint=fingerprint,
        title=body.title,
        decision=body.decision,
        severity=body.severity,
        project_id=body.project_id,
        task_id=body.task_id,
    )
    return {"status": "recorded", "fingerprint": fingerprint}


@router.get("/stats")
async def get_stats(request: Request, user_id: str = Depends(require_user)):
    db = _db(request)
    return await feedback_stats(db, user_id)
