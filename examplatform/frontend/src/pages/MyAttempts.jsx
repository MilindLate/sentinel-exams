import { useEffect, useState } from 'react'
import { useLocation } from 'react-router-dom'
import api from '../services/api'

const STATUS_BADGE = {
  in_progress: 'badge-muted',
  submitted: 'badge-muted',
  evaluated: 'badge-ok',
  flagged: 'badge-danger',
}

export default function MyAttempts() {
  const [attempts, setAttempts] = useState([])
  const [loading, setLoading] = useState(true)
  const location = useLocation()
  const justSubmitted = location.state?.justSubmitted

  useEffect(() => {
    api.get('/attempts/my')
      .then(({ data }) => setAttempts(data))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="page">
      <div className="page-header">
        <p className="eyebrow">Your Record</p>
        <h1>My Results</h1>
        <p>Scores and integrity outcomes for every exam you've taken.</p>
      </div>

      {justSubmitted && (
        <div className="success-banner">
          Exam submitted. Score: {justSubmitted.score}% · Integrity score: {justSubmitted.integrity_score.toFixed(0)}
        </div>
      )}

      {loading && <p style={{ color: 'var(--text-dim)' }}>Loading…</p>}

      {!loading && attempts.length === 0 && (
        <div className="empty-state card">
          <div className="icon">📄</div>
          <p>You haven't taken any exams yet.</p>
        </div>
      )}

      {attempts.length > 0 && (
        <div className="card">
          <table>
            <thead>
              <tr>
                <th>Attempt</th>
                <th>Started</th>
                <th>Status</th>
                <th>Score</th>
                <th>Integrity</th>
              </tr>
            </thead>
            <tbody>
              {attempts.map((a) => (
                <tr key={a.id}>
                  <td>#{a.id} (Exam {a.exam_id})</td>
                  <td>{new Date(a.started_at).toLocaleString()}</td>
                  <td><span className={`badge ${STATUS_BADGE[a.status] || 'badge-muted'}`}>{a.status.replace('_', ' ')}</span></td>
                  <td>{a.score !== null ? `${a.score}%` : '—'}</td>
                  <td>{a.integrity_score.toFixed(0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
