import React, { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { apiGet } from '../lib/api'
import Card from '../components/Card'
import Button from '../components/Button'

export default function PaymentSuccessPage(){
  const [params] = useSearchParams()
  const sessionId = params.get('session_id')
  return (
    <div className="container page" style={{ maxWidth:720 }}>
      <div style={{ textAlign:'center', padding:'12px 0 18px' }}>
        <div style={{ width:64, height:64, borderRadius:'50%', background:'rgba(107,195,154,0.12)', color:'#8FE3B7', display:'grid', placeItems:'center', margin:'0 auto 14px', border:'1px solid rgba(107,195,154,0.22)' }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M5 13l4 4L19 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
        </div>
        <p className="eyebrow">Paiement reçu</p>
        <h1 style={{ fontFamily:'var(--font-display)', fontSize:'2rem', marginTop:6 }}>Merci — votre réservation est confirmée.</h1>
        <p className="muted" style={{ marginTop:10, lineHeight:1.6, maxWidth:48, marginInline:'auto' }}>
          Nous avons bien reçu votre paiement. Vous recevrez une confirmation par e-mail et une notification sous peu. Vous pouvez suivre votre séjour depuis « Mes réservations ».
        </p>
        {sessionId && <p className="small muted" style={{ marginTop:8 }}>Référence de session : <code style={{ background:'rgba(255,255,255,0.06)', padding:'2px 6px', borderRadius:6, border:'1px solid var(--color-border)', color:'var(--color-text-secondary)' }}>{sessionId.slice(0,12)}…</code></p>}
      </div>

      <Card>
        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          <h3 style={{ fontFamily:'var(--font-display)', fontSize:'1.05rem' }}>Prochaines étapes</h3>
          <ul className="small muted" style={{ paddingLeft:18, lineHeight:1.8 }}>
            <li>Un e-mail de confirmation est en cours d'envoi.</li>
            <li>Votre facture et les détails du séjour sont disponibles dans « Mes réservations ».</li>
            <li>Besoin d'aide ? Notre assistance reste joignable.</li>
          </ul>
          <div style={{ display:'flex', gap:10, flexWrap:'wrap', marginTop:6 }}>
            <Button as="a" href="/mes-reservations">Voir mes réservations</Button>
            <Link to="/" className="btn btn-secondary">Retour à l'accueil</Link>
          </div>
        </div>
      </Card>
    </div>
  )
}
