// Field.jsx — Wrapper label + input + error
// Props: label, htmlFor, error?, hint?, children (input element), className, required?
import React from 'react'

export default function Field({ label, htmlFor, error, hint, children, className = '', required = false }) {
  const id = htmlFor || `field-${Math.random().toString(36).slice(2, 9)}`

  return (
    <div className={`field ${className}`}>
      {label && (
        <label htmlFor={id} className="field-label">
          {label}
          {required && <span aria-hidden="true" style={{ color: 'var(--color-danger)', marginLeft: '0.25rem' }}>*</span>}
        </label>
      )}
      <div>
        {React.isValidElement(children) ? React.cloneElement(children, { id, 'aria-invalid': !!error, 'aria-describedby': error ? `${id}-error` : hint ? `${id}-hint` : undefined }) : children}
        {error && <p id={`${id}-error`} className="field-error" role="alert">{error}</p>}
        {hint && !error && <p id={`${id}-hint`} className="field-hint">{hint}</p>}
      </div>
    </div>
  )
}