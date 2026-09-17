// Modal.jsx — Modal avec overlay, fermeture Escape/backdrop
// Props: open, onClose, title, children, footer?, size='sm'|'md'|'lg', className
import React, { useEffect, useCallback } from 'react'

const sizeClasses = {
  sm: 'max-w-md',
  md: 'max-w-2xl',
  lg: 'max-w-4xl'
}

export default function Modal({ open, onClose, title, children, footer, size = 'md', className = '' }) {
  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose()
  }, [onClose])

  useEffect(() => {
    if (open) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden'
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = ''
    }
  }, [open, handleKeyDown])

  if (!open) return null

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div className="modal-overlay" onClick={handleOverlayClick} role="dialog" aria-modal="true" aria-labelledby={title ? 'modal-title' : undefined}>
      <div className={`modal ${sizeClasses[size] || sizeClasses.md} ${className}`}>
        {title && (
          <div className="modal-header">
            <h2 id="modal-title" className="modal-title">{title}</h2>
            <button type="button" className="modal-close" onClick={onClose} aria-label="Fermer">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                <path d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" />
              </svg>
            </button>
          </div>
        )}
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  )
}