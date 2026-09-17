// Layout.jsx — Chrome partagé (header, nav, footer, outlet)
import React, { useState } from 'react'
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import Footer from './Footer'

export default function Layout() {
  const { isAuthenticated, user, logout } = useAuth()
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()

  const navLinks = [
    { to: '/', label: 'Accueil' },
    { to: '/actualites', label: 'Actualités' },
    { to: { pathname: '/', hash: '#hebergements' }, label: 'Hébergements' },
    { to: { pathname: '/', hash: '#a-propos' }, label: 'À propos' },
    { to: { pathname: '/', hash: '#destinations' }, label: 'Destinations' },
    { to: { pathname: '/', hash: '#comment-ca-marche' }, label: 'Comment ça marche' },
    { to: { pathname: '/', hash: '#avis' }, label: 'Avis' },
  ]
  const authLinks = isAuthenticated
    ? [
        { to: '/mes-reservations', label: 'Mes réservations' },
        { to: '/favoris', label: 'Favoris' },
        { to: '/notifications', label: 'Notifications' },
        { to: '/profil', label: 'Profil' },
      ]
    : [
        { to: '/connexion', label: 'Connexion' },
        { to: '/inscription', label: 'Inscription' },
      ]
  const managerLinks = user && (user.role === 'hotel_manager' || user.role === 'admin' || user.is_staff) ? [{ to: '/back-office', label: 'Back-office' }] : []

  const handleLogout = async () => {
    await logout()
    setMenuOpen(false)
    navigate('/')
  }

  const closeMenu = () => setMenuOpen(false)

  const handleNavClick = (link) => {
    if (typeof link.to === 'object' && link.to.hash && location.pathname === '/' && window.location.hash === link.to.hash) {
      // Same anchor on home — smooth-scroll to that section
      const id = link.to.hash.slice(1)
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else if (typeof link.to === 'string' && link.to === '/') {
      // Accueil — always return to first screen (hero), even when already on home scrolled down
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  const isHome = location.pathname === '/'
  return (
    <div className="page-layout">
      <header className={`site-header ${isHome ? 'site-header--hero' : ''}`} role="banner">
        <div className="container site-header-inner">
          <NavLink to="/" className="site-logo" aria-label="Hôtel Lumière — Accueil" onClick={() => { closeMenu(); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
            <span className="site-logo-mark">H</span>
            Hôtel Lumière
          </NavLink>

          <nav className="site-nav" role="navigation" aria-label="Navigation principale">
            {navLinks.map((link) => (
              <NavLink
                key={typeof link.to === 'string' ? link.to : `${link.to.pathname}${link.to.hash}`}
                to={link.to}
                className={({ isActive }) => `site-nav-link ${isActive ? 'active' : ''}`}
                end={typeof link.to === 'string' && link.to === '/'}
                onClick={() => handleNavClick(link)}
              >
                {link.label}
              </NavLink>
            ))}
            {authLinks.map((link) => (
              <NavLink key={link.to} to={link.to} className={({ isActive }) => `site-nav-link auth-link ${isActive ? 'active' : ''}`}>
                {link.label}
              </NavLink>
            ))}
            {managerLinks.map((link) => (
              <NavLink key={link.to} to={link.to} className={({ isActive }) => `site-nav-link auth-link ${isActive ? 'active' : ''}`}>
                {link.label}
              </NavLink>
            ))}
            {isAuthenticated && (
              <button type="button" className="btn btn-ghost btn-sm" onClick={handleLogout} style={{ marginLeft: 4 }}>
                Déconnexion
              </button>
            )}
          </nav>

          <button type="button" className="mobile-toggle" aria-label={menuOpen ? 'Fermer le menu' : 'Ouvrir le menu'} aria-expanded={menuOpen} onClick={() => setMenuOpen((v) => !v)}>
            {menuOpen ? (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M4 4l12 12M16 4L4 16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
            ) : (
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M3 6h14M3 10h14M3 14h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" /></svg>
            )}
          </button>
        </div>
      </header>

      {menuOpen && (
        <div className="mobile-drawer" role="dialog" aria-label="Menu">
          <nav aria-label="Navigation mobile">
            {[...navLinks, ...authLinks, ...managerLinks].map((link) => (
              <NavLink
                key={typeof link.to === 'string' ? link.to : `${link.to.pathname}${link.to.hash}-${link.label}`}
                to={link.to}
                className={({ isActive }) => `site-nav-link ${isActive ? 'active' : ''}`}
                onClick={() => { handleNavClick(link); closeMenu() }}
              >
                {link.label}
              </NavLink>
            ))}
            {isAuthenticated && (
              <button type="button" className="btn btn-secondary" onClick={handleLogout} style={{ marginTop: 8 }}>
                Déconnexion
              </button>
            )}
          </nav>
        </div>
      )}

      <main className="site-main" role="main">
        <Outlet />
      </main>

      <Footer />
    </div>
  )
}
