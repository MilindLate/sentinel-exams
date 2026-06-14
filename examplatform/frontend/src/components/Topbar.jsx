import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Topbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  if (!user) return null

  const isTeacher = user.role === 'teacher' || user.role === 'admin'

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const isActive = (path) => location.pathname.startsWith(path)

  return (
    <header className="topbar">
      <div className="brand">
        <span className="dot" />
        SENTINEL EXAMS
      </div>
      <nav className="nav-links">
        <Link to="/exams" className={isActive('/exams') ? 'active' : ''}>Exams</Link>
        {!isTeacher && (
          <Link to="/my-attempts" className={isActive('/my-attempts') ? 'active' : ''}>My Results</Link>
        )}
        {isTeacher && (
          <Link to="/exams/create" className={isActive('/exams/create') ? 'active' : ''}>Create Exam</Link>
        )}
        <span className="role-badge">{user.role}</span>
        <button className="btn btn-sm" onClick={handleLogout}>Logout</button>
      </nav>
    </header>
  )
}
