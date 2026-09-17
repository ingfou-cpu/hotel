// Badge.jsx — Badge d'état
// Props: color='success'|'warning'|'danger'|'neutral'|'info', children, className
const colorClasses = {
  success: 'badge-success',
  warning: 'badge-warning',
  danger: 'badge-danger',
  neutral: 'badge-neutral',
  info: 'badge-info'
}

export default function Badge({ color = 'neutral', children, className = '' }) {
  const colorClass = colorClasses[color] || colorClasses.neutral
  return (
    <span className={`badge ${colorClass} ${className}`}>
      {children}
    </span>
  )
}