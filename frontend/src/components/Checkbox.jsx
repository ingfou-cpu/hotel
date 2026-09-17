// Checkbox.jsx — Checkbox contrôlé avec forwardRef
// Props: label, error, checked, onChange, onBlur, disabled, required, className, name, id, description (texte après le label), ...rest
import React, { forwardRef } from 'react'

const Checkbox = forwardRef(function Checkbox(
  {
    label,
    error,
    checked = false,
    onChange,
    onBlur,
    disabled = false,
    required = false,
    className = '',
    name,
    id,
    description,
    ...rest
  },
  ref
) {
  const checkboxId = id || name || `checkbox-${Math.random().toString(36).slice(2, 9)}`
  const wrapperClass = `flex items-start gap-2 ${className}`

  return (
    <div className={wrapperClass}>
      <input
        ref={ref}
        type="checkbox"
        id={checkboxId}
        name={name}
        checked={checked}
        onChange={onChange}
        onBlur={onBlur}
        disabled={disabled}
        required={required}
        className="mt-1 h-4 w-4 rounded border-gray-300 text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2 transition-colors"
        aria-invalid={!!error}
        aria-describedby={error ? `${checkboxId}-error` : undefined}
        {...rest}
      />
      <div className="flex flex-col">
        <label htmlFor={checkboxId} className="text-sm font-medium text-gray-900 cursor-pointer select-none">
          {label}
          {required && <span aria-hidden="true" className="text-red-600 ml-1">*</span>}
        </label>
        {description && <p className="text-sm text-gray-500 mt-0.5">{description}</p>}
        {error && <p id={`${checkboxId}-error`} className="text-sm text-red-600 mt-0.5" role="alert">{error}</p>}
      </div>
    </div>
  )
})

Checkbox.displayName = 'Checkbox'

export default Checkbox