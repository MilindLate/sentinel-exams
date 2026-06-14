from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.models import (
    Exam, ExamAttempt, Answer, Question, User, UserRole,
    AttemptStatus, QuestionType,
)
from app.schemas.schemas import AttemptStart, AttemptSubmit, AttemptOut

router = APIRouter(prefix="/api/attempts", tags=["attempts"])


@router.post("/start", response_model=AttemptOut)
def start_attempt(
    payload: AttemptStart,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.STUDENT)),
):
    exam = db.query(Exam).filter(Exam.id == payload.exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")

    existing = (
        db.query(ExamAttempt)
        .filter(
            ExamAttempt.exam_id == exam.id,
            ExamAttempt.student_id == user.id,
            ExamAttempt.status == AttemptStatus.IN_PROGRESS,
        )
        .first()
    )
    if existing:
        return existing

    attempt = ExamAttempt(exam_id=exam.id, student_id=user.id)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.post("/{attempt_id}/submit", response_model=AttemptOut)
def submit_attempt(
    attempt_id: int,
    payload: AttemptSubmit,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.STUDENT)),
):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.student_id != user.id:
        raise HTTPException(status_code=403, detail="Not your attempt")
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Attempt already submitted")

    questions = {q.id: q for q in attempt.exam.questions}
    total_marks = 0.0
    scored_marks = 0.0

    for ans in payload.answers:
        question = questions.get(ans.question_id)
        if not question:
            continue
        total_marks += question.marks
        is_correct = None
        marks_awarded = 0.0

        if question.type in (QuestionType.MCQ, QuestionType.TRUE_FALSE):
            is_correct = ans.response.strip().lower() == question.correct_answer.strip().lower()
            marks_awarded = question.marks if is_correct else 0.0
        # SHORT_ANSWER left for manual/AI grading -> marks_awarded stays 0, is_correct None

        scored_marks += marks_awarded
        db.add(Answer(
            attempt_id=attempt.id,
            question_id=question.id,
            response=ans.response,
            is_correct=is_correct,
            marks_awarded=marks_awarded,
        ))

    attempt.score = round((scored_marks / total_marks) * 100, 2) if total_marks > 0 else 0.0
    attempt.status = AttemptStatus.EVALUATED
    attempt.submitted_at = datetime.utcnow()

    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/{attempt_id}", response_model=AttemptOut)
def get_attempt(attempt_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    attempt = db.query(ExamAttempt).filter(ExamAttempt.id == attempt_id).first()
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")
    if attempt.student_id != user.id and user.role == UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Not allowed")
    return attempt


@router.get("/my", response_model=list[AttemptOut])
def my_attempts(db: Session = Depends(get_db), user: User = Depends(require_role(UserRole.STUDENT))):
    return db.query(ExamAttempt).filter(ExamAttempt.student_id == user.id).all()
