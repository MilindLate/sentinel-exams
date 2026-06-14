import { useEffect, useRef, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import api from '../services/api'

const FRAME_ANALYSIS_INTERVAL_MS = 5000

export default function TakeExam() {
  const { examId } = useParams()
  const navigate = useNavigate()

  const [exam, setExam] = useState(null)
  const [questions, setQuestions] = useState([])
  const [attempt, setAttempt] = useState(null)
  const [answers, setAnswers] = useState({})
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [timeLeft, setTimeLeft] = useState(null)

  const [integrityScore, setIntegrityScore] = useState(100)
  const [events, setEvents] = useState([])
  const [cameraError, setCameraError] = useState('')

  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)

  // ---------- Load exam + start attempt ----------
  useEffect(() => {
    let cancelled = false

    async function init() {
      try {
        const examRes = await api.get(`/exams/${examId}`)
        if (cancelled) return
        setExam(examRes.data)
        setTimeLeft(examRes.data.duration_minutes * 60)

        const qRes = await api.get(`/exams/${examId}/questions`)
        if (cancelled) return
        setQuestions(qRes.data)

        const attemptRes = await api.post('/attempts/start', { exam_id: Number(examId) })
        if (cancelled) return
        setAttempt(attemptRes.data)
        setIntegrityScore(attemptRes.data.integrity_score)
      } catch (err) {
        setError(err.response?.data?.detail || 'Failed to load exam.')
      } finally {
        setLoading(false)
      }
    }

    init()
    return () => { cancelled = true }
  }, [examId])

  // ---------- Timer ----------
  useEffect(() => {
    if (timeLeft === null || attempt?.status !== 'in_progress') return
    if (timeLeft <= 0) {
      handleSubmit()
      return
    }
    const t = setTimeout(() => setTimeLeft((s) => s - 1), 1000)
    return () => clearTimeout(t)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [timeLeft, attempt])

  // ---------- Camera setup ----------
  useEffect(() => {
    if (!exam?.proctoring_enabled || !attempt) return

    let stream
    navigator.mediaDevices?.getUserMedia({ video: true })
      .then((s) => {
        stream = s
        streamRef.current = s
        if (videoRef.current) videoRef.current.srcObject = s
      })
      .catch(() => setCameraError('Camera access denied. Proctoring will run without video.'))

    return () => {
      stream?.getTracks().forEach((t) => t.stop())
    }
  }, [exam, attempt])

  // ---------- Frame analysis loop ----------
  const captureAndAnalyze = useCallback(async () => {
    if (!videoRef.current || !canvasRef.current || !attempt) return
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video.videoWidth) return

    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
    const dataUrl = canvas.toDataURL('image/jpeg', 0.6)

    try {
      const { data } = await api.post('/proctoring/analyze-frame', {
        attempt_id: attempt.id,
        image_base64: dataUrl,
      })
      if (data.flagged_events.length > 0) {
        setEvents((prev) => [
          ...data.flagged_events.map((ev) => ({ type: ev, time: new Date().toLocaleTimeString() })),
          ...prev,
        ].slice(0, 20))

        const severityMap = { face_not_detected: 5, multiple_faces: 10, looking_away: 2 }
        setIntegrityScore((prev) => {
          let next = prev
          for (const ev of data.flagged_events) {
            next = Math.max(0, next - (severityMap[ev] || 1) * 0.5)
          }
          return next
        })
      }
    } catch {
      // Non-fatal; proctoring continues
    }
  }, [attempt])

  useEffect(() => {
    if (!exam?.proctoring_enabled || !attempt || attempt.status !== 'in_progress') return
    const interval = setInterval(captureAndAnalyze, FRAME_ANALYSIS_INTERVAL_MS)
    return () => clearInterval(interval)
  }, [exam, attempt, captureAndAnalyze])

  // ---------- Tab switch / copy-paste detection ----------
  useEffect(() => {
    if (!exam?.proctoring_enabled || !attempt) return

    const logEvent = async (eventType, severity) => {
      setEvents((prev) => [{ type: eventType, time: new Date().toLocaleTimeString() }, ...prev].slice(0, 20))
      setIntegrityScore((prev) => Math.max(0, prev - severity * 0.5))
      try {
        await api.post('/proctoring/event', {
          attempt_id: attempt.id,
          event_type: eventType,
          severity,
          meta: {},
        })
      } catch {
        // non-fatal
      }
    }

    const onVisibilityChange = () => {
      if (document.hidden) logEvent('tab_switch', 8)
    }
    const onCopy = () => logEvent('copy_paste', 10)
    const onPaste = () => logEvent('copy_paste', 10)

    document.addEventListener('visibilitychange', onVisibilityChange)
    document.addEventListener('copy', onCopy)
    document.addEventListener('paste', onPaste)

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange)
      document.removeEventListener('copy', onCopy)
      document.removeEventListener('paste', onPaste)
    }
  }, [exam, attempt])

  // ---------- Answer handling ----------
  const setAnswer = (questionId, response) => {
    setAnswers((prev) => ({ ...prev, [questionId]: response }))
  }

  const handleSubmit = async () => {
    if (!attempt || submitting) return
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        answers: questions.map((q) => ({
          question_id: q.id,
          response: answers[q.id] || '',
        })),
      }
      const { data } = await api.post(`/attempts/${attempt.id}/submit`, payload)
      streamRef.current?.getTracks().forEach((t) => t.stop())
      navigate('/my-attempts', { state: { justSubmitted: data } })
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit attempt.')
    } finally {
      setSubmitting(false)
    }
  }

  const formatTime = (s) => {
    const m = Math.floor(s / 60)
    const sec = s % 60
    return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
  }

  if (loading) return <div className="page"><p style={{ color: 'var(--text-dim)' }}>Loading exam…</p></div>
  if (error && !exam) return <div className="page"><div className="error-banner">{error}</div></div>

  const integrityColor = integrityScore > 70 ? 'var(--ok)' : integrityScore > 40 ? 'var(--warn)' : 'var(--danger)'

  return (
    <div className="page">
      <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p className="eyebrow">Live Attempt</p>
          <h1>{exam.title}</h1>
          <p>{questions.length} questions · {exam.duration_minutes} minutes</p>
        </div>
        <div style={{ textAlign: 'right' }}>
          <div className="timer">{timeLeft !== null ? formatTime(timeLeft) : '--:--'}</div>
          <p style={{ color: 'var(--text-dim)', fontSize: 12, margin: 0 }}>Time remaining</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}
      {attempt?.status === 'flagged' && (
        <div className="error-banner">
          This attempt has been flagged for review due to integrity violations. You may continue and submit.
        </div>
      )}

      <div className="exam-layout">
        <div className="card">
          {questions.map((q, idx) => (
            <div className="question-block" key={q.id}>
              <div className="question-number">QUESTION {idx + 1} · {q.marks} mark{q.marks !== 1 ? 's' : ''}</div>
              <p style={{ margin: '0 0 4px', fontSize: 15 }}>{q.text}</p>

              {q.type === 'mcq' && q.options.map((opt) => (
                <div
                  key={opt}
                  className={`option-row ${answers[q.id] === opt ? 'selected' : ''}`}
                  onClick={() => setAnswer(q.id, opt)}
                >
                  <input type="radio" checked={answers[q.id] === opt} readOnly />
                  {opt}
                </div>
              ))}

              {q.type === 'true_false' && ['true', 'false'].map((opt) => (
                <div
                  key={opt}
                  className={`option-row ${answers[q.id] === opt ? 'selected' : ''}`}
                  onClick={() => setAnswer(q.id, opt)}
                >
                  <input type="radio" checked={answers[q.id] === opt} readOnly />
                  {opt === 'true' ? 'True' : 'False'}
                </div>
              ))}

              {q.type === 'short_answer' && (
                <textarea
                  rows={3}
                  style={{ marginTop: 8 }}
                  value={answers[q.id] || ''}
                  onChange={(e) => setAnswer(q.id, e.target.value)}
                  placeholder="Type your answer…"
                />
              )}
            </div>
          ))}

          <button className="btn btn-primary" onClick={handleSubmit} disabled={submitting} style={{ marginTop: 16 }}>
            {submitting ? 'Submitting…' : 'Submit exam'}
          </button>
        </div>

        {exam.proctoring_enabled && (
          <div className="proctor-panel card">
            <p className="eyebrow">Proctoring</p>
            <video ref={videoRef} className="proctor-feed" autoPlay muted playsInline />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            {cameraError && <p style={{ color: 'var(--warn)', fontSize: 12, marginTop: 8 }}>{cameraError}</p>}

            <div className="integrity-meter">
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: 'var(--text-dim)' }}>
                <span>Integrity score</span>
                <span style={{ color: integrityColor, fontFamily: 'var(--font-mono)' }}>{integrityScore.toFixed(0)}</span>
              </div>
              <div className="integrity-bar">
                <div className="integrity-fill" style={{ width: `${integrityScore}%`, background: integrityColor }} />
              </div>
            </div>

            <p className="eyebrow" style={{ marginTop: 16 }}>Event log</p>
            <div className="event-log">
              {events.length === 0 && <div style={{ color: 'var(--text-dim)' }}>No flags recorded.</div>}
              {events.map((ev, i) => (
                <div key={i}>{ev.time} — {ev.type.replaceAll('_', ' ')}</div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
