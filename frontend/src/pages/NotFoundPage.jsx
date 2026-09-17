import React from 'react'
import { Link } from 'react-router-dom'

export default function NotFoundPage(){
  return (
    <div className="container page" style={{ maxWidth:720, textAlign:'center', padding:'48px 20px' }}>
      <div style={{ width:72, height:72, borderRadius:'50%', background:'var(--color-surface-warm)', border:'1px solid var(--color-border)', display:'grid', placeItems:'center', margin:'0 auto 16px', color:'var(--color-accent)', fontFamily:'var(--font-display)', fontWeight:700, fontSize:'1.6rem' }}>404</div>
      <p className="eyebrow">Page introuvable</p>
      <h1 style={{ fontFamily:'var(--font-display)', fontSize:'2rem', marginTop:6 }}>Cette page n'existe pas.</h1>
      <p className="muted" style={{ marginTop:10, lineHeight:1.6, maxWidth:42, marginInline:'auto' }}>L'adresse saisie est incorrecte ou le contenu a été déplacé. Retournez à l'accueil pour poursuivre votre recherche.</p>
      <div style={{ marginTop:18, display:'flex', gap:10, justifyContent:'center', flexWrap:'wrap' }}>
        <Link to="/" className="btn btn-primary">Retour à l'accueil</Link>
        <Link to="/mes-reservations" className="btn btn-secondary">Mes réservations</Link>
      </div>
    </div>
  )
}
