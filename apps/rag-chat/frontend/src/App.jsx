import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider, Login, Register, ForgotPassword, AuthGuard } from '@ui/components'
import Chat from './pages/Chat'
import AuthCallback from './pages/AuthCallback'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8082'

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
                <Chat />
              </AuthGuard>
            }
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App

