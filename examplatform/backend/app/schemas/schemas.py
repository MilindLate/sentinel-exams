from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, EmailStr

from app.models.models import UserRole, QuestionType, AttemptStatus, ProctoringEventType


# ---------- Auth ----------
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: UserRole = UserRole.STUDENT


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ---------- Questions ----------
class QuestionCreate(BaseModel):
    text: str
    type: QuestionType = QuestionType.MCQ
    options: list[str] = []
    correct_answer: str
    marks: float = 1.0


class QuestionOut(BaseModel):
    id: int
    text: str
    type: QuestionType
    options: list[str]
    marks: float

    class Config:
        from_attributes = True


class QuestionWithAnswerOut(QuestionOut):
    correct_answer: str


# ---------- Exams ----------
class ExamCreate(BaseModel):
    title: str
    description: str = ""
    duration_minutes: int = 60
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    proctoring_enabled: bool = True
    questions: list[QuestionCreate] = []


class ExamOut(BaseModel):
    id: int
    title: str
    description: str
    duration_minutes: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    proctoring_enabled: bool
    created_by: int

    class Config:
        from_attributes = True


class ExamDetailOut(ExamOut):
    questions: list[QuestionOut]


# ---------- Attempts ----------
class AttemptStart(BaseModel):
    exam_id: int


class AnswerSubmit(BaseModel):
    question_id: int
    response: str


class AttemptSubmit(BaseModel):
    answers: list[AnswerSubmit]


class AttemptOut(BaseModel):
    id: int
    exam_id: int
    student_id: int
    started_at: datetime
    submitted_at: Optional[datetime]
    status: AttemptStatus
    score: Optional[float]
    integrity_score: float

    class Config:
        from_attributes = True


# ---------- Proctoring ----------
class ProctoringEventCreate(BaseModel):
    attempt_id: int
    event_type: ProctoringEventType
    severity: float = 1.0
    meta: dict[str, Any] = {}


class ProctoringEventOut(BaseModel):
    id: int
    event_type: ProctoringEventType
    severity: float
    timestamp: datetime
    meta: dict[str, Any]

    class Config:
        from_attributes = True


class FrameAnalysisRequest(BaseModel):
    attempt_id: int
    image_base64: str


class FrameAnalysisResult(BaseModel):
    faces_detected: int
    looking_away: bool
    flagged_events: list[str]


# ---------- Analytics ----------
class ExamAnalytics(BaseModel):
    exam_id: int
    total_attempts: int
    average_score: float
    highest_score: float
    lowest_score: float
    pass_rate: float
    average_integrity_score: float
    flagged_attempts: int


class StudentAnalytics(BaseModel):
    student_id: int
    total_exams_taken: int
    average_score: float
    average_integrity_score: float
