// Button.jsx — Bouton polyvalent
// Props: variant='primary'|'secondary'|'ghost'|'danger', size='sm'|'md'|'lg', loading?, disabled?, as='button'|'a', href?, children, onClick, className, type='button'|'submit'|'reset'
import React from 'react'

const variantClasses = {
  primary: 'btn-primary',
  secondary: 'btn-secondary',
  ghost: 'btn-ghost',
  danger: 'btn-danger'
}

const sizeClasses = {
  sm: 'btn-sm',
  md: '',
  lg: 'btn-lg'
}

export default function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled = false,
  as = 'button',
  href,
  children,
  onClick,
  className = '',
  type = 'button',
  ...rest
}) {
  const baseClass = 'btn'
  const variantClass = variantClasses[variant] || variantClasses.primary
  const sizeClass = sizeClasses[size] || ''
  const classNames = [baseClass, variantClass, sizeClass, className].filter(Boolean).join(' ')

  const handleClick = (e) => {
    if (disabled || loading) {
      e.preventDefault()
      return
    }
    onClick?.(e)
  }

  if (as === 'a' && href) {
    return (
      <a
        href={href}
        className={classNames}
        onClick={handleClick}
        aria-disabled={disabled || loading}
        {...rest}
      >
        {loading && <span className="spinner spinner-sm" aria-hidden="true" />}
        {children}
      </a>
    )
  }

  // `as` can also be a component (e.g. react-router <Link>) — render it polymorphically
  if (typeof as !== 'string') {
    const Tag = as
    return (
      <Tag
        className={classNames}
        onClick={handleClick}
        aria-disabled={disabled || loading}
        {...rest}
      >
        {loading && <span className="spinner spinner-sm" aria-hidden="true" />}
        {children}
      </Tag>
    )
  }

  return (
    <button
      type={type}
      className={classNames}
      disabled={disabled || loading}
      onClick={handleClick}
      {...rest}
    >
      {loading && <span className="spinner spinner-sm" aria-hidden="true" />}
      {children}
    </button>
  )
}