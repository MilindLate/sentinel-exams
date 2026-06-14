from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import ExamAttempt, ProctoringEvent, ProctoringEventType, User, AttemptStatus
from app.schemas.schemas import (
    ProctoringEventCreate, ProctoringEventOut, FrameAnalysisRequest, FrameAnalysisResult,
)
from app.proctoring.frame_analysis import analyze_frame

router = APIRouter(prefix="/api/proctoring", tags=["proctoring"])

# Severity penalty applied to integrity score per flagged event
SEVERITY_MAP = {
    "face_not_detected": 5.0,
    "multiple_faces": 10.0,
    "looking_away": 2.0,
    "tab_switch": 8.0,
    "noise_detected": 3.0,
    "copy_paste": 10.0,
}

FLAG_THRESHOLD = 40.0  # integrity score below which attempt is auto-flagged


@router.post("/analyze-frame", response_model=FrameAnalysisResult)
def analyze_proctoring_frame(
    payload: FrameAnalysisRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == payload.attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.student_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")

    result = analyze_frame(payload.image_base64)

    for event_name in result["flagged_events"]:
        if event_name not in SEVERITY_MAP:
            continue
        severity = SEVERITY_MAP[event_name]
        event = ProctoringEvent(
            attempt_id=attempt.id,
            event_type=ProctoringEventType(event_name),
            severity=severity,
            meta={"source": "frame_analysis"},
        )
        db.add(event)
        attempt.integrity_score = max(0.0, attempt.integrity_score - severity * 0.5)

    if attempt.integrity_score < FLAG_THRESHOLD and attempt.status == AttemptStatus.IN_PROGRESS:
        attempt.status = AttemptStatus.FLAGGED

    db.commit()
    return FrameAnalysisResult(**result)


@router.post("/event", response_model=ProctoringEventOut)
def log_proctoring_event(
    payload: ProctoringEventCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """For client-side events: tab switches, copy-paste, etc."""
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == payload.attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.student_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")

    event = ProctoringEvent(
        attempt_id=attempt.id,
        event_type=payload.event_type,
        severity=payload.severity,
        meta=payload.meta,
    )
    db.add(event)

    attempt.integrity_score = max(0.0, attempt.integrity_score - event.severity * 0.5)
    if attempt.integrity_score < FLAG_THRESHOLD and attempt.status == AttemptStatus.IN_PROGRESS:
        attempt.status = AttemptStatus.FLAGGED

    db.commit()
    db.refresh(event)
    return event


@router.get("/attempts/{attempt_id}/events", response_model=list[ProctoringEventOut])
def get_attempt_events(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.student_id != user.id and user.role.value == "student":
        raise HTTPException(status_code=403, detail="Not allowed")
    return attempt.proctoring_events
