import React, { useState } from 'react'
import { Link } from 'react-router-dom'

export default function Footer() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    const trimmed = email.trim()
    const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmed)
    if (!valid) {
      setError('Veuillez saisir une adresse e-mail valide.')
      setSuccess('')
      return
    }
    setError('')
    setSuccess('Merci ! Votre inscription est bien notée.')
    setEmail('')
  }

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="container">
        <div className="footer-grid">
          <div className="footer-brand">
            <Link to="/" className="footer-logo" aria-label="Hôtel Lumière — Accueil">
              <span className="site-logo-mark">H</span>
              Hôtel Lumière
            </Link>
            <p className="footer-blurb">Séjours d'exception, de Paris aux Alpes.</p>
          </div>

          <nav className="footer-col" aria-label="Découvrir">
            <h3 className="footer-title">Découvrir</h3>
            <ul className="footer-links">
              <li><Link to="/">Accueil</Link></li>
              <li><Link to={{ pathname: '/', hash: '#a-propos' }}>À propos</Link></li>
              <li><Link to={{ pathname: '/', hash: '#destinations' }}>Destinations</Link></li>
              <li><Link to={{ pathname: '/', hash: '#hebergements' }}>Hébergements</Link></li>
            </ul>
          </nav>

          <nav className="footer-col" aria-label="Aide">
            <h3 className="footer-title">Aide</h3>
            <ul className="footer-links">
              <li><Link to="/connexion">Connexion</Link></li>
              <li><Link to="/inscription">Inscription</Link></li>
              <li><Link to="/mes-reservations">Mes réservations</Link></li>
            </ul>
          </nav>

          <div className="footer-newsletter">
            <h3 className="footer-title">Restez inspiré</h3>
            <form noValidate onSubmit={handleSubmit} className="newsletter-form">
              <label htmlFor="footer-newsletter-email" className="visually-hidden">Adresse e-mail</label>
              <div className="newsletter-field">
                <input
                  id="footer-newsletter-email"
                  type="email"
                  className={`field-input newsletter-input${error ? ' error' : ''}`}
                  placeholder="Votre e-mail"
                  value={email}
                  onChange={(e) => { setEmail(e.target.value); if (error) setError('') }}
                  aria-invalid={!!error}
                  aria-describedby={error ? 'footer-newsletter-error' : success ? 'footer-newsletter-success' : undefined}
                  autoComplete="email"
                />
                <button type="submit" className="btn btn-primary btn-sm newsletter-btn">S'abonner</button>
              </div>
              {error && <p id="footer-newsletter-error" className="field-error newsletter-msg" role="alert">{error}</p>}
              {success && <p id="footer-newsletter-success" className="newsletter-success" role="status">{success}</p>}
            </form>
          </div>
        </div>

        <div className="footer-legal">
          <p>© 2026 Hôtel Lumière — Séjours d'exception. Tous droits réservés.</p>
          <div className="site-footer-links">
            <span className="small muted">Paiement sécurisé</span>
            <span className="small muted">Assistance 7j/7</span>
          </div>
        </div>
      </div>
    </footer>
  )
}
