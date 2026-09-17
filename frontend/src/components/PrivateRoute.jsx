// PrivateRoute.jsx — Route protégée (auth requise)
// Props: children
import React from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'

export default function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  if (loading) {
    return (
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <span className="spinner spinner-lg" aria-label="Vérification de l'authentification" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/connexion" state={{ from: location }} replace />
  }

  return children
}