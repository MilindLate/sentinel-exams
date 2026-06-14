import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import api from '../services/api'

export default function ExamAnalytics() {
  const { examId } = useParams()
  const [exam, setExam] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([
      api.get(`/exams/${examId}`),
      api.get(`/analytics/exams/${examId}`),
    ])
      .then(([examRes, analyticsRes]) => {
        setExam(examRes.data)
        setAnalytics(analyticsRes.data)
      })
      .catch((err) => setError(err.response?.data?.detail || 'Failed to load analytics.'))
      .finally(() => setLoading(false))
  }, [examId])

  if (loading) return <div className="page"><p style={{ color: 'var(--text-dim)' }}>Loading…</p></div>
  if (error) return <div className="page"><div className="error-banner">{error}</div></div>

  const chartData = [
    { name: 'Average', value: analytics.average_score },
    { name: 'Highest', value: analytics.highest_score },
    { name: 'Lowest', value: analytics.lowest_score },
  ]

  return (
    <div className="page">
      <div className="page-header">
        <p className="eyebrow">Analytics</p>
        <h1>{exam.title}</h1>
        <p>Performance and integrity summary across all submitted attempts.</p>
      </div>

      {analytics.total_attempts === 0 ? (
        <div className="empty-state card">
          <div className="icon">📊</div>
          <p>No attempts submitted yet for this exam.</p>
        </div>
      ) : (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <p className="stat-label">Total Attempts</p>
              <p className="stat-value">{analytics.total_attempts}</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Average Score</p>
              <p className="stat-value">{analytics.average_score}%</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Pass Rate</p>
              <p className="stat-value">{analytics.pass_rate}%</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Avg Integrity</p>
              <p className="stat-value">{analytics.average_integrity_score}</p>
            </div>
            <div className="stat-card">
              <p className="stat-label">Flagged Attempts</p>
              <p className="stat-value" style={{ color: analytics.flagged_attempts > 0 ? 'var(--danger)' : 'var(--text)' }}>
                {analytics.flagged_attempts}
              </p>
            </div>
          </div>

          <div className="card" style={{ height: 320 }}>
            <p className="card-title">Score Distribution</p>
            <ResponsiveContainer width="100%" height="85%">
              <BarChart data={chartData}>
                <CartesianGrid stroke="#2a313c" strokeDasharray="3 3" />
                <XAxis dataKey="name" stroke="#8b96a5" fontSize={12} />
                <YAxis stroke="#8b96a5" fontSize={12} domain={[0, 100]} />
                <Tooltip
                  contentStyle={{ background: '#161b22', border: '1px solid #2a313c', borderRadius: 6, fontSize: 12 }}
                  labelStyle={{ color: '#e6e9ef' }}
                />
                <Bar dataKey="value" fill="#ff5c39" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </>
      )}
    </div>
  )
}
