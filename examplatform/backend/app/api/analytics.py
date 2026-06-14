from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.models import Exam, ExamAttempt, User, UserRole, AttemptStatus
from app.schemas.schemas import ExamAnalytics, StudentAnalytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

PASS_THRESHOLD = 40.0


@router.get("/exams/{exam_id}", response_model=ExamAnalytics)
def exam_analytics(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    attempts = db.query(ExamAttempt).filter(
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.status.in_([AttemptStatus.EVALUATED, AttemptStatus.FLAGGED]),
    ).all()

    if not attempts:
        return ExamAnalytics(
            exam_id=exam_id, total_attempts=0, average_score=0, highest_score=0,
            lowest_score=0, pass_rate=0, average_integrity_score=0, flagged_attempts=0,
        )

    scores = [a.score or 0.0 for a in attempts]
    integrity_scores = [a.integrity_score for a in attempts]
    flagged = sum(1 for a in attempts if a.status == AttemptStatus.FLAGGED)
    passed = sum(1 for s in scores if s >= PASS_THRESHOLD)

    return ExamAnalytics(
        exam_id=exam_id,
        total_attempts=len(attempts),
        average_score=round(sum(scores) / len(scores), 2),
        highest_score=max(scores),
        lowest_score=min(scores),
        pass_rate=round((passed / len(attempts)) * 100, 2),
        average_integrity_score=round(sum(integrity_scores) / len(integrity_scores), 2),
        flagged_attempts=flagged,
    )


@router.get("/students/{student_id}", response_model=StudentAnalytics)
def student_analytics(
    student_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if user.role == UserRole.STUDENT and user.id != student_id:
        raise HTTPException(status_code=403, detail="Not allowed")

    attempts = db.query(ExamAttempt).filter(
        ExamAttempt.student_id == student_id,
        ExamAttempt.status.in_([AttemptStatus.EVALUATED, AttemptStatus.FLAGGED]),
    ).all()

    if not attempts:
        return StudentAnalytics(
            student_id=student_id, total_exams_taken=0, average_score=0, average_integrity_score=0,
        )

    scores = [a.score or 0.0 for a in attempts]
    integrity_scores = [a.integrity_score for a in attempts]

    return StudentAnalytics(
        student_id=student_id,
        total_exams_taken=len(attempts),
        average_score=round(sum(scores) / len(scores), 2),
        average_integrity_score=round(sum(integrity_scores) / len(integrity_scores), 2),
    )
