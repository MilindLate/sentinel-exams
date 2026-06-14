def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    resp = client.post("/api/auth/register", json={
        "name": "Teacher One",
        "email": "teacher@example.com",
        "password": "pass1234",
        "role": "teacher",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "teacher@example.com"

    resp = client.post("/api/auth/login", json={
        "email": "teacher@example.com",
        "password": "pass1234",
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_duplicate_registration_fails(client):
    payload = {
        "name": "Dup User",
        "email": "dup@example.com",
        "password": "pass1234",
        "role": "student",
    }
    r1 = client.post("/api/auth/register", json=payload)
    r2 = client.post("/api/auth/register", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 400


def _auth_header(client, email, password, name="User", role="teacher"):
    client.post("/api/auth/register", json={
        "name": name, "email": email, "password": password, "role": role
    })
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_exam_and_take_it(client):
    teacher_headers = _auth_header(client, "teacher2@example.com", "pass1234", role="teacher")
    student_headers = _auth_header(client, "student1@example.com", "pass1234", role="student")

    exam_payload = {
        "title": "Sample Exam",
        "description": "A test exam",
        "duration_minutes": 30,
        "proctoring_enabled": True,
        "questions": [
            {
                "text": "2 + 2 = ?",
                "type": "mcq",
                "options": ["3", "4", "5"],
                "correct_answer": "4",
                "marks": 1.0,
            },
            {
                "text": "The sky is blue.",
                "type": "true_false",
                "options": ["true", "false"],
                "correct_answer": "true",
                "marks": 1.0,
            },
        ],
    }
    resp = client.post("/api/exams", json=exam_payload, headers=teacher_headers)
    assert resp.status_code == 200
    exam = resp.json()
    exam_id = exam["id"]
    questions = exam["questions"]
    assert len(questions) == 2

    # Start attempt as student
    resp = client.post("/api/attempts/start", json={"exam_id": exam_id}, headers=student_headers)
    assert resp.status_code == 200
    attempt = resp.json()
    attempt_id = attempt["id"]
    assert attempt["status"] == "in_progress"

    # Submit answers - one correct, one wrong
    answers = [
        {"question_id": questions[0]["id"], "response": "4"},  # correct
        {"question_id": questions[1]["id"], "response": "false"},  # incorrect
    ]
    resp = client.post(f"/api/attempts/{attempt_id}/submit", json={"answers": answers}, headers=student_headers)
    assert resp.status_code == 200
    result = resp.json()
    assert result["status"] == "evaluated"
    assert result["score"] == 50.0


def test_analytics(client):
    teacher_headers = _auth_header(client, "teacher3@example.com", "pass1234", role="teacher")
    student_headers = _auth_header(client, "student2@example.com", "pass1234", role="student")

    exam_payload = {
        "title": "Analytics Exam",
        "questions": [
            {"text": "Q1", "type": "mcq", "options": ["a", "b"], "correct_answer": "a", "marks": 1.0},
        ],
    }
    resp = client.post("/api/exams", json=exam_payload, headers=teacher_headers)
    exam_id = resp.json()["id"]
    question_id = resp.json()["questions"][0]["id"]

    resp = client.post("/api/attempts/start", json={"exam_id": exam_id}, headers=student_headers)
    attempt_id = resp.json()["id"]

    client.post(
        f"/api/attempts/{attempt_id}/submit",
        json={"answers": [{"question_id": question_id, "response": "a"}]},
        headers=student_headers,
    )

    resp = client.get(f"/api/analytics/exams/{exam_id}", headers=teacher_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_attempts"] == 1
    assert data["average_score"] == 100.0
