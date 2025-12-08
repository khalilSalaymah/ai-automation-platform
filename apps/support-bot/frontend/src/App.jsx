import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider, Login, Register, ForgotPassword, AuthGuard, AdminGuard } from '@ui/components'
import Support from './pages/Support'
import AuthCallback from './pages/AuthCallback'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  return (
    <AuthProvider apiUrl={API_URL}>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route
            path="/"
            element={
              <AuthGuard>
                <Support />
              </AuthGuard>
            }
          />
          <Route
            path="/admin/*"
            element={
              <AdminGuard>
                <Support />
              </AdminGuard>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App

