// Spinner.jsx — Spinner inline
// Props: size='sm'|'md'|'lg', className, ariaLabel
export default function Spinner({ size = 'md', className = '', ariaLabel = 'Chargement' }) {
  const sizeClass = size === 'sm' ? 'spinner-sm' : size === 'lg' ? 'spinner-lg' : ''
  return (
    <span
      className={`spinner ${sizeClass} ${className}`}
      role="status"
      aria-label={ariaLabel}
    >
      <span className="visually-hidden">{ariaLabel}</span>
    </span>
  )
}