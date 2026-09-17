// EmptyState.jsx — État vide avec icône, titre, description, action
// Props: icon (ReactNode), title, description?, action?, className
import React from 'react'

export default function EmptyState({ icon, title, description, action, className = '' }) {
  return (
    <div className={`empty-state ${className}`} style={{ padding: '3rem 1.5rem' }}>
      {icon && <div className="empty-state-icon" aria-hidden="true">{icon}</div>}
      {title && <h3 className="empty-state-title">{title}</h3>}
      {description && <p className="empty-state-description">{description}</p>}
      {action && <div style={{ marginTop: '1rem' }}>{action}</div>}
    </div>
  )
}