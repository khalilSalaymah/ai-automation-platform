import { Navigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export const AuthGuard = ({ children, requireRole = null }) => {
  const { isAuthenticated, user, loading } = useAuth()

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requireRole && user?.role !== requireRole) {
    return <Navigate to="/" replace />
  }

  return children
}

export const AdminGuard = ({ children }) => {
  return <AuthGuard requireRole="admin">{children}</AuthGuard>
}


