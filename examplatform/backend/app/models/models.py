import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean, Enum, JSON
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.STUDENT, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    exams_created = relationship("Exam", back_populates="creator")
    attempts = relationship("ExamAttempt", back_populates="student")


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, default="")
    duration_minutes = Column(Integer, default=60)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    proctoring_enabled = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    creator = relationship("User", back_populates="exams_created")
    questions = relationship("Question", back_populates="exam", cascade="all, delete-orphan")
    attempts = relationship("ExamAttempt", back_populates="exam")


class QuestionType(str, enum.Enum):
    MCQ = "mcq"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    text = Column(Text, nullable=False)
    type = Column(Enum(QuestionType), default=QuestionType.MCQ)
    options = Column(JSON, default=list)
    correct_answer = Column(Text, nullable=False)
    marks = Column(Float, default=1.0)

    exam = relationship("Exam", back_populates="questions")


class AttemptStatus(str, enum.Enum):
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    EVALUATED = "evaluated"
    FLAGGED = "flagged"


class ExamAttempt(Base):
    __tablename__ = "exam_attempts"

    id = Column(Integer, primary_key=True, index=True)
    exam_id = Column(Integer, ForeignKey("exams.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)
    status = Column(Enum(AttemptStatus), default=AttemptStatus.IN_PROGRESS)
    score = Column(Float, nullable=True)
    integrity_score = Column(Float, default=100.0)

    exam = relationship("Exam", back_populates="attempts")
    student = relationship("User", back_populates="attempts")
    answers = relationship("Answer", back_populates="attempt", cascade="all, delete-orphan")
    proctoring_events = relationship("ProctoringEvent", back_populates="attempt", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    response = Column(Text, default="")
    is_correct = Column(Boolean, nullable=True)
    marks_awarded = Column(Float, default=0.0)

    attempt = relationship("ExamAttempt", back_populates="answers")
    question = relationship("Question")


class ProctoringEventType(str, enum.Enum):
    FACE_NOT_DETECTED = "face_not_detected"
    MULTIPLE_FACES = "multiple_faces"
    LOOKING_AWAY = "looking_away"
    TAB_SWITCH = "tab_switch"
    NOISE_DETECTED = "noise_detected"
    COPY_PASTE = "copy_paste"


class ProctoringEvent(Base):
    __tablename__ = "proctoring_events"

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey("exam_attempts.id"))
    event_type = Column(Enum(ProctoringEventType), nullable=False)
    severity = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    meta = Column(JSON, default=dict)

    attempt = relationship("ExamAttempt", back_populates="proctoring_events")
