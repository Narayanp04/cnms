import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../services/api'
import toast from 'react-hot-toast'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('accessToken'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      fetchUser()
    } else {
      setLoading(false)
    }
  }, [token])

  const fetchUser = async () => {
    try {
      const { data } = await api.get('/api/v1/auth/me')
      setUser(data)
    } catch (error) {
      console.error('Failed to fetch user:', error)
      logout()
    } finally {
      setLoading(false)
    }
  }

  const login = async (username, password) => {
    try {
      const { data } = await api.post('/api/v1/auth/login', { username, password })
      localStorage.setItem('accessToken', data.access_token)
      localStorage.setItem('refreshToken', data.refresh_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
      setToken(data.access_token)
      setUser(data.user)
      toast.success(`Welcome back, ${data.user.full_name || data.user.username}!`)
      return data
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed'
      toast.error(message)
      throw error
    }
  }

  const logout = useCallback(() => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
    delete api.defaults.headers.common['Authorization']
    setToken(null)
    setUser(null)
  }, [])

  const refreshToken = async () => {
    try {
      const refreshToken = localStorage.getItem('refreshToken')
      if (!refreshToken) throw new Error('No refresh token')
      
      const { data } = await api.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      })
      localStorage.setItem('accessToken', data.access_token)
      localStorage.setItem('refreshToken', data.refresh_token)
      api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
      setToken(data.access_token)
      setUser(data.user)
      return data
    } catch (error) {
      logout()
      throw error
    }
  }

  const hasRole = (roles) => {
    if (!user) return false
    return roles.includes(user.role)
  }

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      logout,
      refreshToken,
      hasRole,
      isAuthenticated: !!user,
      isAdmin: user?.role === 'admin',
      isOperator: user?.role === 'operator' || user?.role === 'admin'
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
