from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import get_current_user, require_role
from app.models.models import Exam, Question, User, UserRole
from app.schemas.schemas import ExamCreate, ExamOut, ExamDetailOut, QuestionOut

router = APIRouter(prefix="/api/exams", tags=["exams"])


@router.post("", response_model=ExamDetailOut)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    exam = Exam(
        title=payload.title,
        description=payload.description,
        duration_minutes=payload.duration_minutes,
        start_time=payload.start_time,
        end_time=payload.end_time,
        proctoring_enabled=payload.proctoring_enabled,
        created_by=user.id,
    )
    db.add(exam)
    db.flush()

    for q in payload.questions:
        question = Question(
            exam_id=exam.id,
            text=q.text,
            type=q.type,
            options=q.options,
            correct_answer=q.correct_answer,
            marks=q.marks,
        )
        db.add(question)

    db.commit()
    db.refresh(exam)
    return exam


@router.get("", response_model=list[ExamOut])
def list_exams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Exam).all()


@router.get("/{exam_id}", response_model=ExamDetailOut)
def get_exam(exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam


@router.get("/{exam_id}/questions", response_model=list[QuestionOut])
def get_exam_questions(exam_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Student-facing: returns questions WITHOUT correct answers."""
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    return exam.questions


@router.delete("/{exam_id}")
def delete_exam(
    exam_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(UserRole.ADMIN, UserRole.TEACHER)),
):
    exam = db.query(Exam).filter(Exam.id == exam_id).first()
    if not exam:
        raise HTTPException(status_code=404, detail="Exam not found")
    if exam.created_by != user.id and user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Not allowed")
    db.delete(exam)
    db.commit()
    return {"detail": "Exam deleted"}
