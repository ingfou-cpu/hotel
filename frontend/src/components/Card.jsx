// Card.jsx — Conteneur de carte simple
// Props: title?, children, className, headerAction?, footer?
export default function Card({ title, children, className = '', headerAction, footer }) {
  return (
    <div className={`card ${className}`}>
      {(title || headerAction) && (
        <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          {title && <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600 }}>{title}</h3>}
          {headerAction && <div>{headerAction}</div>}
        </div>
      )}
      <div className="card-body">{children}</div>
      {footer && <div className="card-footer">{footer}</div>}
    </div>
  )
}