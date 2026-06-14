import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import Topbar from './components/Topbar'
import ProtectedRoute from './components/ProtectedRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import ExamList from './pages/ExamList'
import CreateExam from './pages/CreateExam'
import TakeExam from './pages/TakeExam'
import MyAttempts from './pages/MyAttempts'
import ExamAnalytics from './pages/ExamAnalytics'

export default function App() {
  const { user } = useAuth()

  return (
    <div className="app-shell">
      <Topbar />
      <Routes>
        <Route path="/login" element={user ? <Navigate to="/exams" /> : <Login />} />
        <Route path="/register" element={user ? <Navigate to="/exams" /> : <Register />} />

        <Route path="/exams" element={
          <ProtectedRoute><ExamList /></ProtectedRoute>
        } />
        <Route path="/exams/create" element={
          <ProtectedRoute roles={['teacher', 'admin']}><CreateExam /></ProtectedRoute>
        } />
        <Route path="/exams/:examId/take" element={
          <ProtectedRoute roles={['student']}><TakeExam /></ProtectedRoute>
        } />
        <Route path="/exams/:examId/analytics" element={
          <ProtectedRoute roles={['teacher', 'admin']}><ExamAnalytics /></ProtectedRoute>
        } />
        <Route path="/my-attempts" element={
          <ProtectedRoute roles={['student']}><MyAttempts /></ProtectedRoute>
        } />

        <Route path="/" element={<Navigate to="/exams" />} />
        <Route path="*" element={<Navigate to="/exams" />} />
      </Routes>
    </div>
  )
}
