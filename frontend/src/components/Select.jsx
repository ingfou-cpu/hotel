// Select.jsx — Select contrôlé avec forwardRef
// Props: label, error, hint, value, onChange, onBlur, disabled, required, placeholder, options=[{value, label}], className, name, id, ...rest
import React, { forwardRef } from 'react'
import Field from './Field'

const Select = forwardRef(function Select(
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
    options = [],
    className = '',
    name,
    id,
    ...rest
  },
  ref
) {
  const selectId = id || name || `select-${Math.random().toString(36).slice(2, 9)}`

  return (
    <Field label={label} htmlFor={selectId} error={error} hint={hint} required={required}>
      <select
        ref={ref}
        id={selectId}
        name={name}
        value={value}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        required={required}
        className={`field-input ${error ? 'error' : ''} ${className}`}
        {...rest}
      >
        {placeholder && (
          <option value="" disabled>
            {placeholder}
          </option>
        )}
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </Field>
  )
})

Select.displayName = 'Select'

export default Select