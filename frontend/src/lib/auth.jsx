// AuthContext + useAuth hook pour HotelBooking
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { apiGet, apiPost, apiPatch, apiDelete, setAuthFailureHandler } from './api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const isAuthenticated = !!user

  const hydrateUser = useCallback(async () => {
    try {
      const data = await apiGet('/auth/me/')
      setUser(data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    setAuthFailureHandler(() => {
      setUser(null)
      window.location.assign('/connexion')
    })

    const { access } = JSON.parse(localStorage.getItem('hb_access') ? '{"access":true}' : '{}')
    if (localStorage.getItem('hb_access')) {
      hydrateUser()
    } else {
      setLoading(false)
    }
  }, [hydrateUser])

  const login = useCallback(async (email, password) => {
    const data = await apiPost('/auth/login/', { email, password })
    localStorage.setItem('hb_access', data.access)
    localStorage.setItem('hb_refresh', data.refresh)
    const userData = await apiGet('/auth/me/')
    setUser(userData)
    return userData
  }, [])

  const register = useCallback(async ({ email, password, first_name, last_name, phone }) => {
    await apiPost('/auth/register/', { email, password, first_name, last_name, phone })
    return login(email, password)
  }, [login])

  const logout = useCallback(async () => {
    const refresh = localStorage.getItem('hb_refresh')
    if (refresh) {
      try {
        await apiPost('/auth/logout/', { refresh })
      } catch {
        // Ignore logout errors
      }
    }
    localStorage.removeItem('hb_access')
    localStorage.removeItem('hb_refresh')
    setUser(null)
  }, [])

  const refreshUser = useCallback(async () => {
    try {
      const data = await apiGet('/auth/me/')
      setUser(data)
      return data
    } catch {
      setUser(null)
      throw new Error('Session expirée')
    }
  }, [])

  const updateProfile = useCallback(async (patch) => {
    const data = await apiPatch('/auth/me/', patch)
    setUser(data)
    return data
  }, [])

  const changePassword = useCallback(async ({ current_password, new_password, new_password_confirm }) => {
    await apiPost('/auth/change-password/', { current_password, new_password, new_password_confirm })
    await logout()
  }, [logout])

  const deleteAccount = useCallback(async () => {
    await apiDelete('/auth/me/')
    localStorage.removeItem('hb_access')
    localStorage.removeItem('hb_refresh')
    setUser(null)
  }, [])

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshUser,
    updateProfile,
    changePassword,
    deleteAccount
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth doit être utilisé dans un AuthProvider')
  }
  return context
}

export function isManagerOrStaff(user) {
  if (!user) return false
  return user.role === 'hotel_manager' || user.role === 'admin' || user.is_staff === true
}