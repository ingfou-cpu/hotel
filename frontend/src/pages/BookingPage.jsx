import React, { useEffect, useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { apiGet, apiPost, normalizeApiError } from '../lib/api'
import { formatPrice, formatDate, nightsBetween, validateDateRange } from '../lib/format'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Input from '../components/Input'
import Spinner from '../components/Spinner'
import Card from '../components/Card'

export default function BookingPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const hotelId = searchParams.get('hotel')
  const roomId = searchParams.get('room')
  const qCheckIn = searchParams.get('check_in') || ''
  const qCheckOut = searchParams.get('check_out') || ''

  const [hotel, setHotel] = useState(null)
  const [room, setRoom] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState(null)

  const [checkIn, setCheckIn] = useState(qCheckIn)
  const [checkOut, setCheckOut] = useState(qCheckOut)
  const [adults, setAdults] = useState(2)
  const [children, setChildren] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [generalError, setGeneralError] = useState('')
  const [bookingCreated, setBookingCreated] = useState(null)

  useEffect(()=>{
    if(!hotelId || !roomId){
      setError('Paramètres de réservation manquants. Veuillez sélectionner une chambre depuis la page de l\'hôtel.')
      setLoading(false)
      return
    }
    let cancelled=false
    async function fetchData(){
      setLoading(true); setError('')
      try{
        const h = await apiGet(`/hotels/${hotelId}/`)
        if(cancelled) return
        setHotel(h)
        // try rooms endpoint for this room
        try{
          const r = await apiGet(`/rooms/${roomId}/`)
          setRoom(r)
        }catch{
          // fallback: find in hotel rooms
          const found = (h.rooms||[]).find(r=> String(r.id)===String(roomId))
          if(found) setRoom(found)
          else throw new Error('Chambre introuvable')
        }
      }catch(e){
        const {message}=normalizeApiError(e)
        setError(message || 'Impossible de charger la chambre')
      }finally{ if(!cancelled) setLoading(false)}
    }
    fetchData()
    return ()=>{ cancelled=true }
  },[hotelId, roomId])

  const nights = nightsBetween(checkIn, checkOut)
  const pricePerNight = room ? Number(room.price_per_night) : 0
  const subtotal = nights * pricePerNight
  const taxes = subtotal * 0.10
  const fee = nights>0 ? 5.00 : 0
  const estimatedTotal = subtotal + taxes + fee

  const capacityError = room && (adults+children) > room.max_occupancy ? `Capacité dépassée : cette chambre accueille ${room.max_occupancy} personne(s) maximum.` : null
  const dateError = checkIn && checkOut ? validateDateRange(checkIn, checkOut) : null

  const handleSubmit = async (e)=>{
    e.preventDefault()
    setGeneralError(''); setFieldErrors(null)
    if(dateError){ setGeneralError(dateError); return }
    if(capacityError){ setGeneralError(capacityError); return }
    if(!checkIn || !checkOut){ setGeneralError('Veuillez renseigner les dates d\'arrivée et de départ.'); return }
    setSubmitting(true)
    try{
      const booking = await apiPost('/bookings/', { room: Number(roomId), check_in: checkIn, check_out: checkOut, adults: Number(adults), children: Number(children) })
      setBookingCreated(booking)
      // create payment then checkout
      try{
        const payment = await apiPost('/payments/', { booking: booking.id })
        const checkout = await apiPost(`/payments/${payment.id}/checkout/`, {})
        if(checkout.checkout_url){
          window.location.assign(checkout.checkout_url)
          return
        }
      }catch(payErr){
        const {message}=normalizeApiError(payErr)
        // booking succeeded but payment failed — show fallback
        setGeneralError(message ? `Réservation confirmée (${booking.booking_code}) mais le paiement n'a pas pu être initié : ${message}. Vous pourrez payer depuis « Mes réservations ».` : `Réservation ${booking.booking_code} créée. Vous pourrez payer depuis « Mes réservations ».`)
        return
      }
      // if checkout succeeded we redirected; if no URL, navigate to detail
      navigate(`/reservation/${booking.booking_code}`)
    }catch(err){
      const {message, fieldErrors: fe}=normalizeApiError(err)
      if(fe) setFieldErrors(fe)
      setGeneralError(message || 'La réservation n\'a pas pu être créée.')
    }finally{ setSubmitting(false)}
  }

  if(loading) return <div className="container page" style={{ display:'flex', justifyContent:'center', padding:60 }}><Spinner size="lg" /></div>
  if(error) return <div className="container page"><Alert type="error">{error}</Alert><div style={{ marginTop:12 }}><Link to={hotelId ? `/hotels/${hotelId}` : '/'} className="btn btn-secondary">Retour</Link></div></div>

  return (
    <div className="container page">
      <div style={{ marginBottom:16 }}>
        <Link to={hotel ? `/hotels/${hotel.id}` : '/'} className="small muted" style={{ textDecoration:'underline' }}>← Retour à l'hôtel</Link>
      </div>
      <div className="page-header">
        <p className="eyebrow">Réservation</p>
        <h1>Finaliser votre séjour</h1>
        <p>Vérifiez les détails, ajustez les dates et confirmez. Vous serez redirigé vers le paiement sécurisé.</p>
      </div>

      {generalError && <div style={{ marginBottom:16 }}><Alert type={bookingCreated ? 'warning' : 'error'}>{generalError} {bookingCreated && <Link to={`/reservation/${bookingCreated.booking_code}`} style={{ textDecoration:'underline', marginLeft:6 }}>Voir la réservation</Link>}</Alert></div>}

      <div style={{ display:'grid', gridTemplateColumns:'1.2fr 0.8fr', gap:24, alignItems:'start' }}>
        <form onSubmit={handleSubmit} className="card" style={{ padding:0 }}>
          <div className="card-body" style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.15rem' }}>Détails du séjour</h2>

            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <div className="field">
                <label className="field-label" htmlFor="check_in">Arrivée *</label>
                <input id="check_in" type="date" className={`field-input ${fieldErrors?.check_in || dateError ? 'error':''}`} value={checkIn} onChange={e=>setCheckIn(e.target.value)} required />
                {(fieldErrors?.check_in || dateError) && <p className="field-error">{fieldErrors?.check_in || dateError}</p>}
              </div>
              <div className="field">
                <label className="field-label" htmlFor="check_out">Départ *</label>
                <input id="check_out" type="date" className={`field-input ${fieldErrors?.check_out ? 'error':''}`} value={checkOut} onChange={e=>setCheckOut(e.target.value)} required />
                {fieldErrors?.check_out && <p className="field-error">{fieldErrors.check_out}</p>}
              </div>
            </div>

            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <div className="field">
                <label className="field-label" htmlFor="adults">Adultes *</label>
                <select id="adults" className={`field-input ${fieldErrors?.adults ? 'error':''}`} value={adults} onChange={e=>setAdults(Number(e.target.value))}>
                  {[1,2,3,4,5,6].map(n=><option key={n} value={n}>{n}</option>)}
                </select>
                {fieldErrors?.adults && <p className="field-error">{fieldErrors.adults}</p>}
              </div>
              <div className="field">
                <label className="field-label" htmlFor="children">Enfants</label>
                <select id="children" className={`field-input ${fieldErrors?.children ? 'error':''}`} value={children} onChange={e=>setChildren(Number(e.target.value))}>
                  {[0,1,2,3,4].map(n=><option key={n} value={n}>{n}</option>)}
                </select>
                {fieldErrors?.children && <p className="field-error">{fieldErrors.children}</p>}
              </div>
            </div>

            {capacityError && <Alert type="warning">{capacityError}</Alert>}
            {fieldErrors?.room && <Alert type="error">{fieldErrors.room}</Alert>}
            {fieldErrors?.non_field_errors && <Alert type="error">{fieldErrors.non_field_errors}</Alert>}

            <div className="divider" />

            <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
              <Button type="submit" size="lg" loading={submitting} disabled={!!capacityError || !!dateError}>
                Confirmer et payer
              </Button>
              <Button type="button" variant="secondary" onClick={()=> navigate(`/hotels/${hotelId}`)}>Annuler</Button>
            </div>
            <p className="small muted">En confirmant, vous acceptez les conditions d'annulation de l'établissement. Le montant sera prélevé via notre prestataire de paiement sécurisé.</p>
          </div>
        </form>

        <div className="card summary-card" style={{ position:'sticky', top:88 }}>
          <div className="card-header"><h3 style={{ margin:0 }}>Récapitulatif</h3></div>
          <div className="card-body" style={{ display:'flex', flexDirection:'column', gap:10 }}>
            {hotel && room && (
              <>
                <div style={{ display:'flex', gap:12 }}>
                  <div style={{ width:72, height:72, borderRadius:10, overflow:'hidden', background:'rgba(255,255,255,0.04)', border:'1px solid var(--color-border)', flexShrink:0 }}>
                    {(() => { const img = room.images?.[0]?.image || room.images?.[0]?.url || hotel.image; return img ? <img src={img} alt="" style={{ width:'100%', height:'100%', objectFit:'cover' }} onError={e=>{e.currentTarget.style.display='none'}} /> : null })()}
                  </div>
                  <div>
                    <div style={{ fontWeight:700 }}>{hotel.name}</div>
                    <div className="small muted">{hotel.city}, {hotel.country} · {hotel.stars} ★</div>
                    <div className="small" style={{ marginTop:4, fontWeight:600 }}>{room.room_type_display || room.room_type} — {room.room_number}</div>
                  </div>
                </div>
                <div className="divider" style={{ margin:'6px 0' }} />
                <div className="kv"><span>Dates</span><strong>{checkIn ? formatDate(checkIn) : '—'} → {checkOut ? formatDate(checkOut) : '—'}</strong></div>
                <div className="kv"><span>Durée</span><strong>{nights>0 ? `${nights} nuit${nights>1?'s':''}` : '—'}</strong></div>
                <div className="kv"><span>Voyageurs</span><strong>{adults} adulte{adults>1?'s':''}{children? `, ${children} enfant${children>1?'s':''}`:''}</strong></div>
                <div className="kv"><span>Prix par nuit</span><strong>{formatPrice(pricePerNight)}</strong></div>
                <div className="divider" style={{ margin:'6px 0' }} />
                <div className="kv"><span>Sous-total ({nights} × {formatPrice(pricePerNight)})</span><span>{formatPrice(subtotal)}</span></div>
                <div className="kv"><span>Taxes (10 %)</span><span>{formatPrice(taxes)}</span></div>
                <div className="kv"><span>Frais de service</span><span>{formatPrice(fee)}</span></div>
                <div className="total-row"><span>Total estimé</span><span>{formatPrice(estimatedTotal)}</span></div>
                <p className="small muted" style={{ marginTop:8, fontSize:'0.78rem' }}>Montant définitif calculé côté serveur à la confirmation. Taxes et frais inclus.</p>
              </>
            )}
          </div>
        </div>
      </div>
      <style>{`@media(max-width: 860px){ div[style*="gridTemplateColumns:1.2fr"]{ grid-template-columns:1fr !important; } }`}</style>
    </div>
  )
}
