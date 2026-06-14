import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'

const emptyQuestion = () => ({
  text: '',
  type: 'mcq',
  options: ['', '', '', ''],
  correct_answer: '',
  marks: 1,
})

export default function CreateExam() {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [duration, setDuration] = useState(60)
  const [proctoringEnabled, setProctoringEnabled] = useState(true)
  const [questions, setQuestions] = useState([emptyQuestion()])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const navigate = useNavigate()

  const updateQuestion = (idx, field, value) => {
    setQuestions((prev) => {
      const next = [...prev]
      next[idx] = { ...next[idx], [field]: value }
      return next
    })
  }

  const updateOption = (qIdx, oIdx, value) => {
    setQuestions((prev) => {
      const next = [...prev]
      const options = [...next[qIdx].options]
      options[oIdx] = value
      next[qIdx] = { ...next[qIdx], options }
      return next
    })
  }

  const addQuestion = () => setQuestions((prev) => [...prev, emptyQuestion()])
  const removeQuestion = (idx) => setQuestions((prev) => prev.filter((_, i) => i !== idx))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    const cleanedQuestions = questions.map((q) => ({
      ...q,
      marks: Number(q.marks) || 1,
      options: q.type === 'mcq' ? q.options.filter((o) => o.trim() !== '') : (q.type === 'true_false' ? ['true', 'false'] : []),
    }))

    for (const q of cleanedQuestions) {
      if (!q.text.trim() || !q.correct_answer.trim()) {
        setError('Every question needs text and a correct answer.')
        return
      }
      if (q.type === 'mcq' && q.options.length < 2) {
        setError('MCQ questions need at least 2 options.')
        return
      }
    }

    setSubmitting(true)
    try {
      const { data } = await api.post('/exams', {
        title,
        description,
        duration_minutes: Number(duration),
        proctoring_enabled: proctoringEnabled,
        questions: cleanedQuestions,
      })
      navigate(`/exams`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create exam.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <p className="eyebrow">New Exam</p>
        <h1>Create Exam</h1>
        <p>Set up the exam, then add questions below.</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="card">
          <div className="field">
            <label>Title</label>
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </div>
          <div className="field">
            <label>Description</label>
            <textarea rows={2} value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="form-grid">
            <div className="field">
              <label>Duration (minutes)</label>
              <input type="number" min={1} value={duration} onChange={(e) => setDuration(e.target.value)} required />
            </div>
            <div className="field">
              <label>Proctoring</label>
              <select value={proctoringEnabled ? 'yes' : 'no'} onChange={(e) => setProctoringEnabled(e.target.value === 'yes')}>
                <option value="yes">Enabled</option>
                <option value="no">Disabled</option>
              </select>
            </div>
          </div>
        </div>

        {questions.map((q, idx) => (
          <div className="card" key={idx}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="card-title">Question {idx + 1}</h3>
              {questions.length > 1 && (
                <button type="button" className="btn btn-sm btn-danger" onClick={() => removeQuestion(idx)}>Remove</button>
              )}
            </div>

            <div className="field">
              <label>Question text</label>
              <textarea rows={2} value={q.text} onChange={(e) => updateQuestion(idx, 'text', e.target.value)} required />
            </div>

            <div className="form-grid">
              <div className="field">
                <label>Type</label>
                <select value={q.type} onChange={(e) => updateQuestion(idx, 'type', e.target.value)}>
                  <option value="mcq">Multiple choice</option>
                  <option value="true_false">True / False</option>
                  <option value="short_answer">Short answer</option>
                </select>
              </div>
              <div className="field">
                <label>Marks</label>
                <input type="number" min={0.5} step={0.5} value={q.marks} onChange={(e) => updateQuestion(idx, 'marks', e.target.value)} />
              </div>
            </div>

            {q.type === 'mcq' && (
              <div className="field">
                <label>Options</label>
                {q.options.map((opt, oIdx) => (
                  <input
                    key={oIdx}
                    style={{ marginBottom: 8 }}
                    placeholder={`Option ${oIdx + 1}`}
                    value={opt}
                    onChange={(e) => updateOption(idx, oIdx, e.target.value)}
                  />
                ))}
              </div>
            )}

            <div className="field">
              <label>Correct answer {q.type === 'true_false' ? '(true or false)' : ''}</label>
              {q.type === 'true_false' ? (
                <select value={q.correct_answer} onChange={(e) => updateQuestion(idx, 'correct_answer', e.target.value)}>
                  <option value="">Select…</option>
                  <option value="true">True</option>
                  <option value="false">False</option>
                </select>
              ) : (
                <input value={q.correct_answer} onChange={(e) => updateQuestion(idx, 'correct_answer', e.target.value)} required />
              )}
              {q.type === 'short_answer' && (
                <p style={{ fontSize: 12, color: 'var(--text-dim)', marginTop: 6 }}>
                  Short-answer responses are stored for manual review and are not auto-scored.
                </p>
              )}
            </div>
          </div>
        ))}

        <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
          <button type="button" className="btn" onClick={addQuestion}>+ Add question</button>
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? 'Publishing…' : 'Publish exam'}
          </button>
        </div>
      </form>
    </div>
  )
}
