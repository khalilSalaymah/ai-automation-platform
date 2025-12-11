import { useState, useEffect, createContext, useContext } from 'react'

const AuthContext = createContext(null)

export const AuthProvider = ({ children, apiUrl = 'http://localhost:8000' }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState(localStorage.getItem('access_token'))
  const [refreshToken, setRefreshToken] = useState(localStorage.getItem('refresh_token'))

  useEffect(() => {
    if (token) {
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  // Load branding settings when user is authenticated
  useEffect(() => {
    if (user && token) {
      loadBranding()
    }
  }, [user, token])

  const fetchUser = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/auth/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        setUser(userData)
      } else {
        // Token invalid, try refresh
        if (refreshToken) {
          await refreshAccessToken()
        } else {
          logout()
        }
      }
    } catch (error) {
      console.error('Error fetching user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const refreshAccessToken = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (response.ok) {
        const data = await response.json()
        setToken(data.access_token)
        setRefreshToken(data.refresh_token)
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        await fetchUser()
      } else {
        logout()
      }
    } catch (error) {
      console.error('Error refreshing token:', error)
      logout()
    }
  }

  const login = async (email, password) => {
    try {
      const response = await fetch(`${apiUrl}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (response.ok) {
        const data = await response.json()
        setToken(data.access_token)
        setRefreshToken(data.refresh_token)
        localStorage.setItem('access_token', data.access_token)
        localStorage.setItem('refresh_token', data.refresh_token)
        await fetchUser()
        return { success: true }
      } else {
        const error = await response.json()
        return { success: false, error: error.detail || 'Login failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const register = async (email, password, fullName) => {
    try {
      const response = await fetch(`${apiUrl}/api/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          password,
          full_name: fullName,
        }),
      })

      if (response.ok) {
        const userData = await response.json()
        // Auto-login after registration
        return await login(email, password)
      } else {
        const error = await response.json()
        return { success: false, error: error.detail || 'Registration failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    setRefreshToken(null)
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  }

  const forgotPassword = async (email) => {
    try {
      const response = await fetch(`${apiUrl}/api/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      if (response.ok) {
        return { success: true }
      } else {
        const error = await response.json()
        return { success: false, error: error.detail || 'Request failed' }
      }
    } catch (error) {
      return { success: false, error: 'Network error' }
    }
  }

  const googleLogin = () => {
    window.location.href = `${apiUrl}/api/auth/google/login`
  }

  const loadBranding = async () => {
    try {
      const response = await fetch(`${apiUrl}/api/branding/settings`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const data = await response.json()
        
        // Apply theme variables
        if (data.theme_variables) {
          const root = document.documentElement
          if (data.theme_variables.primary_color) {
            root.style.setProperty('--color-primary', data.theme_variables.primary_color)
          }
          if (data.theme_variables.secondary_color) {
            root.style.setProperty('--color-secondary', data.theme_variables.secondary_color)
          }
          if (data.theme_variables.accent_color) {
            root.style.setProperty('--color-accent', data.theme_variables.accent_color)
          }
          if (data.theme_variables.background_color) {
            root.style.setProperty('--color-background', data.theme_variables.background_color)
          }
          if (data.theme_variables.text_color) {
            root.style.setProperty('--color-text', data.theme_variables.text_color)
          }
          if (data.theme_variables.font_family) {
            root.style.setProperty('--font-family', data.theme_variables.font_family)
          }
          if (data.theme_variables.font_size_base) {
            root.style.setProperty('--font-size-base', data.theme_variables.font_size_base)
          }
          if (data.theme_variables.border_radius) {
            root.style.setProperty('--border-radius', data.theme_variables.border_radius)
          }
        }
      }
    } catch (error) {
      // Silently fail - branding is optional
      console.debug('Could not load branding settings:', error)
    }
  }

  const value = {
    user,
    loading,
    isAuthenticated: !!user,
    login,
    register,
    logout,
    forgotPassword,
    googleLogin,
    token,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}



