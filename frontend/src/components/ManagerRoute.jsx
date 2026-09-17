// ManagerRoute.jsx — Route réservée aux gestionnaires/admins
// Props: children
import React from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth, isManagerOrStaff } from '../lib/auth'

export default function ManagerRoute({ children }) {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="container" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <span className="spinner spinner-lg" aria-label="Vérification des permissions" />
      </div>
    )
  }

  if (!user || !isManagerOrStaff(user)) {
    return <Navigate to="/" replace />
  }

  return children
}