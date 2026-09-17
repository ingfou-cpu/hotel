import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { apiGet, apiPost, normalizeApiError } from '../lib/api'
import { formatPrice, formatDate, formatDateTime, nightsBetween } from '../lib/format'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import StatusBadge from '../components/StatusBadge'
import Button from '../components/Button'
import Card from '../components/Card'

export default function BookingDetailPage(){
  const { bookingCode } = useParams()
  const navigate = useNavigate()
  const [booking, setBooking] = useState(null)
  const [payment, setPayment] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [actionLoading, setActionLoading] = useState('')

  const findBooking = async ()=>{
    setLoading(true); setError('')
    try{
      let page=1, found=null, total=0
      // brute scan pages
      while(true){
        const data = await apiGet('/bookings/', { page })
        total=data.count
        const match = data.results.find(b=> b.booking_code===bookingCode)
        if(match){ found=match; break }
        if(!data.next) break
        page+=1
        if(page>50) break // safety
      }
      if(!found) throw new Error('Réservation introuvable')
      setBooking(found)
      // fetch payment matching booking_code
      try{
        let ppage=1, pfound=null
        while(true){
          const pdata = await apiGet('/payments/', { page: ppage })
          const m = pdata.results.find(p=> p.booking_code===bookingCode || String(p.booking)===String(found.id))
          if(m) { pfound=m; break }
          if(!pdata.next) break
          ppage+=1
          if(ppage>20) break
        }
        if(pfound) setPayment(pfound)
      }catch{}
    }catch(e){
      const {message}=normalizeApiError(e)
      setError(message || 'Réservation introuvable')
    } finally{ setLoading(false)}
  }

  useEffect(()=>{ findBooking() },[bookingCode])

  const handlePay = async()=>{
    if(!booking) return
    setActionLoading('pay'); setActionError('')
    try{
      let pid = payment?.id
      if(!pid){
        const created = await apiPost('/payments/', { booking: booking.id })
        pid = created.id
      }
      const checkout = await apiPost(`/payments/${pid}/checkout/`, {})
      if(checkout.checkout_url) window.location.assign(checkout.checkout_url)
      else setActionError('Impossible de créer la session de paiement.')
    }catch(e){
      const {message}=normalizeApiError(e)
      setActionError(message)
    } finally{ setActionLoading('')}
  }

  const handleCancel = async()=>{
    if(!booking) return
    if(!confirm('Confirmer l\'annulation de cette réservation ?')) return
    setActionLoading('cancel'); setActionError('')
    try{
      const res = await apiPost(`/bookings/${booking.id}/cancel/`, {})
      setBooking(res)
    }catch(e){
      const {message}=normalizeApiError(e)
      setActionError(message)
    } finally{ setActionLoading('')}
  }

  if(loading) return <div className="container page" style={{ display:'flex', justifyContent:'center', padding:60 }}><Spinner size="lg" /></div>
  if(error) return <div className="container page"><Alert type="error">{error}</Alert><div style={{ marginTop:12 }}><Link to="/mes-reservations" className="btn btn-secondary">Retour à mes réservations</Link></div></div>
  if(!booking) return null

  const nights = booking.nights ?? nightsBetween(booking.check_in, booking.check_out)

  return (
    <div className="container page">
      <div style={{ marginBottom:14 }}>
        <Link to="/mes-reservations" className="small muted" style={{ textDecoration:'underline' }}>← Mes réservations</Link>
      </div>
      <div className="page-header" style={{ marginBottom:18 }}>
        <p className="eyebrow">Réservation {booking.booking_code}</p>
        <div style={{ display:'flex', alignItems:'center', gap:12, flexWrap:'wrap', marginTop:6 }}>
          <h1 style={{ fontFamily:'var(--font-display)', fontSize:'1.7rem' }}>{booking.hotel.name}</h1>
          <StatusBadge status={booking.status} type="booking" />
          {payment && <StatusBadge status={payment.status} type="payment" />}
        </div>
        <p className="small muted" style={{ marginTop:6 }}>{booking.hotel.city}, {booking.hotel.country} · Chambre {booking.room.room_number} · Créée le {formatDateTime(booking.created_at)}</p>
      </div>

      {actionError && <div style={{ marginBottom:14 }}><Alert type="error">{actionError}</Alert></div>}

      <div style={{ display:'grid', gridTemplateColumns:'1.3fr 0.7fr', gap:20, alignItems:'start' }}>
        <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
          <Card title="Détails du séjour">
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <div><div className="small muted">Arrivée</div><div style={{ fontWeight:700 }}>{formatDate(booking.check_in)}</div></div>
              <div><div className="small muted">Départ</div><div style={{ fontWeight:700 }}>{formatDate(booking.check_out)}</div></div>
              <div><div className="small muted">Durée</div><div style={{ fontWeight:600 }}>{nights} nuit{nights>1?'s':''}</div></div>
              <div><div className="small muted">Voyageurs</div><div style={{ fontWeight:600 }}>{booking.adults} adulte{booking.adults>1?'s':''}{booking.children? `, ${booking.children} enfant${booking.children>1?'s':''}`:''}</div></div>
            </div>
            <div className="divider" />
            <div style={{ display:'flex', justifyContent:'space-between', gap:12, fontSize:'0.92rem' }}>
              <span className="muted">Prix par nuit</span><span style={{ fontWeight:600 }}>{formatPrice(booking.price_per_night)}</span>
            </div>
          </Card>

          <Card title="Tarification">
            <div className="kv"><span>Sous-total</span><span>{formatPrice(Number(booking.price_per_night)*nights)}</span></div>
            <div className="kv"><span>Taxes</span><span>{formatPrice(booking.tax_amount)}</span></div>
            <div className="kv"><span>Frais de service</span><span>{formatPrice(booking.service_fee)}</span></div>
            <div className="total-row"><span>Total</span><span>{formatPrice(booking.total_price)}</span></div>
            {payment && (
              <>
                <div className="divider" />
                <div className="small muted">Paiement : {payment.status_display || payment.status} · {formatPrice(payment.amount)} {payment.currency?.toUpperCase()}</div>
              </>
            )}
          </Card>
        </div>

        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          <Card>
            <h3 style={{ fontFamily:'var(--font-display)', fontSize:'1.05rem', marginBottom:8 }}>Actions</h3>
            <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
              {booking.status==='pending' && (!payment || payment.status!=='paid') && (
                <Button onClick={handlePay} loading={actionLoading==='pay'}>Payer maintenant</Button>
              )}
              {(booking.status==='pending' || booking.status==='confirmed') && (
                <Button variant="secondary" onClick={handleCancel} loading={actionLoading==='cancel'}>Annuler la réservation</Button>
              )}
              <Link to="/mes-reservations" className="btn btn-ghost" style={{ textAlign:'center' }}>Retour à la liste</Link>
            </div>
            <p className="small muted" style={{ marginTop:10, fontSize:'0.78rem', lineHeight:1.5 }}>Annulation soumise au délai de {2} jour(s) avant l'arrivée. En cas de paiement déjà effectué, un remboursement sera tenté automatiquement.</p>
          </Card>

          <Card>
            <div className="small muted">Référence</div>
            <div style={{ fontWeight:700, letterSpacing:'0.02em' }}>{booking.booking_code}</div>
            <div className="small muted" style={{ marginTop:6 }}>Conservez cette référence pour toute demande d'assistance.</div>
          </Card>
        </div>
      </div>
      <style>{`@media(max-width: 860px){ div[style*="gridTemplateColumns:1.3fr"]{ grid-template-columns:1fr !important; } }`}</style>
    </div>
  )
}
