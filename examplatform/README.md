# Sentinel Exams — Secure, Fair & Intelligent Examination Platform

A full-stack exam platform covering **examination management**, **AI-assisted proctoring**, and **performance analytics**.

## Architecture

```
examplatform/
├── backend/                 FastAPI (Python) REST API
│   ├── app/
│   │   ├── api/             Routers: auth, exams, attempts, proctoring, analytics
│   │   ├── core/             Config, DB session, security/JWT
│   │   ├── models/            SQLAlchemy ORM models
│   │   ├── schemas/            Pydantic request/response schemas
│   │   └── proctoring/         OpenCV-based webcam frame analysis
│   ├── tests/                  Pytest suite (auth, exams, attempts, analytics)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                  React + Vite SPA
│   ├── src/
│   │   ├── pages/              Login, Register, ExamList, CreateExam, TakeExam, MyAttempts, ExamAnalytics
│   │   ├── components/         Topbar, ProtectedRoute
│   │   ├── context/            AuthContext (JWT session)
│   │   └── services/           Axios API client
│   ├── Dockerfile (Nginx)
│   └── nginx.conf
├── docker-compose.yml          Postgres + backend + frontend, one command up
└── .github/workflows/          CI (test/lint/build) + CD (Docker image publish)
```

## Features

### 1. Examination Management
- Role-based accounts: admin / teacher / student (JWT auth, bcrypt password hashing)
- Teachers create exams with MCQ, true/false, and short-answer questions, durations, and proctoring toggle
- Students browse and take exams; auto-grading for objective question types

### 2. AI-Assisted Proctoring
- Live webcam feed captured every 5 seconds, sent to backend for analysis
- OpenCV Haar-cascade face detection: flags face_not_detected, multiple_faces, looking_away
- Browser-side integrity signals: tab_switch (visibility change), copy_paste
- Each event reduces a per-attempt integrity score (0-100); attempts below threshold are auto-flagged for review
- Live integrity meter and event log shown to the student during the exam

### 3. Analytics
- Per-exam dashboard: total attempts, average/highest/lowest score, pass rate, average integrity score, flagged attempt count
- Score distribution bar chart (Recharts)
- Per-student analytics endpoint for transcript-style views

## Running locally

### Option A - Docker Compose (recommended)

```bash
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API docs: http://localhost:8000/docs
- Postgres: localhost:5432 (user/pass: exam_user / exam_pass)

### Option B - Manual

Backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

## CI/CD

- backend-ci.yml - runs pytest + ruff on every push/PR touching backend/
- frontend-ci.yml - runs npm run build on every push/PR touching frontend/
- docker-publish.yml - builds and pushes backend and frontend images to GitHub Container Registry on push to main or version tags

## API overview

| Area | Endpoints |
|---|---|
| Auth | POST /api/auth/register, POST /api/auth/login |
| Exams | POST /api/exams, GET /api/exams, GET /api/exams/{id}, GET /api/exams/{id}/questions, DELETE /api/exams/{id} |
| Attempts | POST /api/attempts/start, POST /api/attempts/{id}/submit, GET /api/attempts/{id}, GET /api/attempts/my |
| Proctoring | POST /api/proctoring/analyze-frame, POST /api/proctoring/event, GET /api/proctoring/attempts/{id}/events |
| Analytics | GET /api/analytics/exams/{id}, GET /api/analytics/students/{id} |

## Notes & next steps

- Short-answer questions are stored but not auto-graded - wire up an LLM-based grader in app/api/attempts.py for that.
- looking_away detection currently uses a simple eye-visibility heuristic; swap in MediaPipe FaceMesh (already in requirements.txt) for gaze-vector estimation.
- Add Alembic migrations for schema changes beyond the initial create_all.
- Add rate limiting / refresh tokens for production hardening.
