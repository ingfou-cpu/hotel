// Input.jsx — Input contrôlé avec forwardRef
// Props: label, error, hint, type='text'|'email'|'password'|'number'|'date'|'tel', value, onChange, onBlur, disabled, required, placeholder, className, name, id, autoComplete, ...rest
import React, { forwardRef } from 'react'
import Field from './Field'

const Input = forwardRef(function Input(
  {
    label,
    error,
    hint,
    type = 'text',
    value = '',
    onChange,
    onBlur,
    disabled = false,
    required = false,
    placeholder = '',
    className = '',
    name,
    id,
    autoComplete,
    ...rest
  },
  ref
) {
  const inputId = id || name || `input-${Math.random().toString(36).slice(2, 9)}`

  return (
    <Field label={label} htmlFor={inputId} error={error} hint={hint} required={required}>
      <input
        ref={ref}
        type={type}
        id={inputId}
        name={name}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        required={required}
        placeholder={placeholder}
        autoComplete={autoComplete}
        className={`field-input ${error ? 'error' : ''} ${className}`}
        {...rest}
      />
    </Field>
  )
})

Input.displayName = 'Input'

export default Input