import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function ExamList() {
  const [exams, setExams] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const { user } = useAuth()
  const isTeacher = user.role === 'teacher' || user.role === 'admin'

  useEffect(() => {
    api.get('/exams')
      .then(({ data }) => setExams(data))
      .catch(() => setError('Could not load exams.'))
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async (id) => {
    if (!confirm('Delete this exam?')) return
    await api.delete(`/exams/${id}`)
    setExams((prev) => prev.filter((e) => e.id !== id))
  }

  return (
    <div className="page">
      <div className="page-header">
        <p className="eyebrow">Exam Catalog</p>
        <h1>Available Exams</h1>
        <p>{isTeacher ? 'Exams you and your colleagues have published.' : 'Pick an exam to begin a proctored attempt.'}</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {loading && <p style={{ color: 'var(--text-dim)' }}>Loading…</p>}

      {!loading && exams.length === 0 && (
        <div className="empty-state card">
          <div className="icon">🗒️</div>
          <p>No exams yet.</p>
          {isTeacher && <Link to="/exams/create" className="btn btn-primary">Create your first exam</Link>}
        </div>
      )}

      <div className="card-grid">
        {exams.map((exam) => (
          <div className="card" key={exam.id}>
            <h3 className="card-title">{exam.title}</h3>
            <p className="card-meta">
              {exam.duration_minutes} min · {exam.proctoring_enabled ? 'Proctored' : 'Unproctored'}
            </p>
            <p style={{ fontSize: 13, color: 'var(--text-dim)', marginBottom: 14 }}>
              {exam.description || 'No description provided.'}
            </p>
            <div style={{ display: 'flex', gap: 8 }}>
              {!isTeacher && (
                <Link to={`/exams/${exam.id}/take`} className="btn btn-primary btn-sm">Start exam</Link>
              )}
              {isTeacher && (
                <>
                  <Link to={`/exams/${exam.id}/analytics`} className="btn btn-sm">Analytics</Link>
                  <button className="btn btn-sm btn-danger" onClick={() => handleDelete(exam.id)}>Delete</button>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
