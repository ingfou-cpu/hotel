import React from 'react'
import { Link } from 'react-router-dom'
import Card from '../components/Card'
import Button from '../components/Button'

export default function PaymentCancelPage(){
  return (
    <div className="container page" style={{ maxWidth:720 }}>
      <div style={{ textAlign:'center', padding:'12px 0 18px' }}>
        <div style={{ width:64, height:64, borderRadius:'50%', background:'#FFF1CC', color:'#9A6B1A', display:'grid', placeItems:'center', margin:'0 auto 14px', border:'1px solid #F5E0A0' }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M12 8v5M12 16h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0z" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/></svg>
        </div>
        <p className="eyebrow">Paiement annulé</p>
        <h1 style={{ fontFamily:'var(--font-display)', fontSize:'2rem', marginTop:6 }}>Paiement annulé ou expiré.</h1>
        <p className="muted" style={{ marginTop:10, lineHeight:1.6, maxWidth:48, marginInline:'auto' }}>
          Votre paiement n'a pas été finalisé. Votre réservation reste en attente : vous pouvez la régler à tout moment depuis « Mes réservations ».
        </p>
      </div>

      <Card>
        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          <h3 style={{ fontFamily:'var(--font-display)', fontSize:'1.05rem' }}>Que faire maintenant ?</h3>
          <ul className="small muted" style={{ paddingLeft:18, lineHeight:1.8 }}>
            <li>Retournez dans « Mes réservations » et appuyez sur « Payer ».</li>
            <li>En cas de prélèvement, aucun montant n'a été débité.</li>
            <li>Besoin d'aide ? Contactez notre assistance.</li>
          </ul>
          <div style={{ display:'flex', gap:10, flexWrap:'wrap', marginTop:6 }}>
            <Button as="a" href="/mes-reservations">Retour à mes réservations</Button>
            <Link to="/" className="btn btn-secondary">Parcourir les hôtels</Link>
          </div>
        </div>
      </Card>
    </div>
  )
}
