// Alert.jsx — Alerte dismissible
// Props: type='success'|'error'|'info'|'warning', children, dismissible?, onDismiss, className
import React from 'react'

const typeClasses = {
  success: 'alert-success',
  error: 'alert-error',
  info: 'alert-info',
  warning: 'alert-warning'
}

export default function Alert({ type = 'info', children, dismissible = false, onDismiss, className = '' }) {
  const typeClass = typeClasses[type] || typeClasses.info
  const dismissibleClass = dismissible ? 'alert-dismissible' : ''

  return (
    <div className={`alert ${typeClass} ${dismissibleClass} ${className}`} role="alert">
      <div style={{ flex: 1 }}>{children}</div>
      {dismissible && (
        <button
          type="button"
          className="alert-close"
          onClick={onDismiss}
          aria-label="Fermer"
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
            <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
          </svg>
        </button>
      )}
    </div>
  )
}