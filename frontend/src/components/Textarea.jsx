// Textarea.jsx — Textarea contrôlé avec forwardRef
// Props: label, error, hint, value, onChange, onBlur, disabled, required, placeholder, rows, className, name, id, ...rest
import React, { forwardRef } from 'react'
import Field from './Field'

const Textarea = forwardRef(function Textarea(
  {
    label,
    error,
    hint,
    value = '',
    onChange,
    onBlur,
    disabled = false,
    required = false,
    placeholder = '',
    rows = 4,
    className = '',
    name,
    id,
    ...rest
  },
  ref
) {
  const textareaId = id || name || `textarea-${Math.random().toString(36).slice(2, 9)}`

  return (
    <Field label={label} htmlFor={textareaId} error={error} hint={hint} required={required}>
      <textarea
        ref={ref}
        id={textareaId}
        name={name}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        required={required}
        placeholder={placeholder}
        rows={rows}
        className={`field-input ${error ? 'error' : ''} ${className}`}
        style={{ resize: 'vertical', minHeight: `${rows * 1.5}rem` }}
        {...rest}
      />
    </Field>
  )
})

Textarea.displayName = 'Textarea'

export default Textarea