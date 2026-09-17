import React, { useEffect, useState, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { apiGet, apiPost, normalizeApiError } from '../lib/api'
import { formatPrice, formatDate } from '../lib/format'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import EmptyState from '../components/EmptyState'
import Pagination from '../components/Pagination'
import StatusBadge from '../components/StatusBadge'
import Button from '../components/Button'

const TABS = [
  { key:'', label:'Toutes' },
  { key:'pending', label:'En attente' },
  { key:'confirmed', label:'Confirmées' },
  { key:'cancelled', label:'Annulées' },
  { key:'completed', label:'Terminées' },
]
const PAGE_SIZE = 20

export default function MyBookingsPage(){
  const [searchParams, setSearchParams] = useSearchParams()
  const status = searchParams.get('status') || ''
  const page = parseInt(searchParams.get('page') || '1', 10) || 1

  const [data, setData] = useState({ results:[], count:0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [actionError, setActionError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const fetchData = useCallback(async()=>{
    setLoading(true); setError('')
    try{
      const params={ page }
      if(status) params.status=status
      const res = await apiGet('/bookings/', params)
      setData(res)
    }catch(e){
      const {message}=normalizeApiError(e); setError(message)
    } finally{ setLoading(false)}
  },[status, page])

  useEffect(()=>{ fetchData() },[fetchData])

  const setStatus = (s)=>{
    const next = new URLSearchParams(searchParams)
    if(s) next.set('status', s); else next.delete('status')
    next.delete('page')
    setSearchParams(next)
  }
  const setPage = (p)=>{
    const next = new URLSearchParams(searchParams)
    next.set('page', String(p))
    setSearchParams(next)
  }

  const handleCancel = async(booking)=>{
    if(!confirm(`Annuler la réservation ${booking.booking_code} ?`)) return
    setBusyId(booking.id); setActionError('')
    try{
      await apiPost(`/bookings/${booking.id}/cancel/`, {})
      fetchData()
    }catch(e){
      const {message}=normalizeApiError(e); setActionError(message)
    } finally{ setBusyId(null)}
  }

  const handlePay = async(booking)=>{
    setBusyId(booking.id); setActionError('')
    try{
      // check existing payment list quickly: try create, if exists handle
      let paymentId
      try{
        const p = await apiPost('/payments/', { booking: booking.id })
        paymentId = p.id
      }catch(e){
        // if already exists, fetch payments to find it
        let pageN=1, found=null
        while(true){
          const pdata = await apiGet('/payments/', { page: pageN })
          const m = pdata.results.find(x=> String(x.booking)===String(booking.id) || x.booking_code===booking.booking_code)
          if(m){ found=m; break }
          if(!pdata.next) break
          pageN+=1
          if(pageN>10) break
        }
        if(found) paymentId=found.id
        else throw e
      }
      const checkout = await apiPost(`/payments/${paymentId}/checkout/`, {})
      if(checkout.checkout_url) window.location.assign(checkout.checkout_url)
      else setActionError('Impossible de créer la session de paiement.')
    }catch(e){
      const {message}=normalizeApiError(e); setActionError(message)
    } finally{ setBusyId(null)}
  }

  const pageCount = Math.max(1, Math.ceil((data.count||0)/PAGE_SIZE))

  return (
    <div className="container page">
      <div className="page-header">
        <p className="eyebrow">Vos séjours</p>
        <h1>Mes réservations</h1>
        <p>Suivez l'état de vos réservations, réglez vos séjours en attente ou annulez selon les conditions.</p>
      </div>

      <div style={{ display:'flex', gap:8, flexWrap:'wrap', marginBottom:16 }}>
        {TABS.map(t=>(
          <button
            key={t.key}
            onClick={()=> setStatus(t.key)}
            className={`chip ${status===t.key ? 'active' : ''}`}
            style={{
              background: status===t.key ? 'var(--color-accent)' : 'var(--color-surface)',
              color: status===t.key ? '#fff' : 'var(--color-text-secondary)',
              borderColor: status===t.key ? 'var(--color-accent)' : 'var(--color-border)',
              cursor:'pointer',
              padding:'8px 14px',
              fontWeight:700
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {error && <div style={{ marginBottom:12 }}><Alert type="error">{error}</Alert></div>}
      {actionError && <div style={{ marginBottom:12 }}><Alert type="error">{actionError}</Alert></div>}

      {loading ? (
        <div style={{ display:'flex', justifyContent:'center', padding:40 }}><Spinner size="lg" /></div>
      ) : data.results.length===0 ? (
        <EmptyState
          title="Aucune réservation"
          description={status ? `Aucune réservation avec le statut « ${TABS.find(t=>t.key===status)?.label} ».` : 'Vous n\'avez pas encore de réservation. Parcourez nos hôtels pour commencer.'}
          action={<Link to="/" className="btn btn-primary">Découvrir les hôtels</Link>}
        />
      ) : (
        <>
          <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {data.results.map(b=>(
              <div key={b.id} className="card" style={{ padding:0 }}>
                <div className="card-body" style={{ display:'grid', gridTemplateColumns:'1fr auto', gap:16, alignItems:'center' }}>
                  <div>
                    <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
                      <Link to={`/reservation/${b.booking_code}`} style={{ fontWeight:700, fontFamily:'var(--font-display)', fontSize:'1.05rem', color:'var(--color-text)', textDecoration:'none' }}>{b.hotel.name}</Link>
                      <StatusBadge status={b.status} type="booking" />
                      <span className="small muted">{b.booking_code}</span>
                    </div>
                    <div className="small muted" style={{ marginTop:4 }}>
                      {b.hotel.city}, {b.hotel.country} · Chambre {b.room.room_number} · {formatDate(b.check_in)} → {formatDate(b.check_out)} · {b.adults + (b.children? `+${b.children}`:'')} pers.
                    </div>
                    <div style={{ marginTop:6, fontWeight:700 }}>{formatPrice(b.total_price)} <span className="small muted" style={{ fontWeight:400 }}>· {b.nights} nuit{b.nights>1?'s':''}</span></div>
                  </div>
                  <div style={{ display:'flex', flexDirection:'column', gap:8, minWidth:160 }}>
                    <Link to={`/reservation/${b.booking_code}`} className="btn btn-secondary btn-sm" style={{ textAlign:'center' }}>Voir le détail</Link>
                    {b.status==='pending' && <Button size="sm" loading={busyId===b.id} onClick={()=>handlePay(b)}>Payer</Button>}
                    {(b.status==='pending' || b.status==='confirmed') && <Button variant="ghost" size="sm" loading={busyId===b.id} onClick={()=>handleCancel(b)}>Annuler</Button>}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <Pagination page={page} pageCount={pageCount} total={data.count} onChange={setPage} />
        </>
      )}
      <style>{`@media(max-width: 640px){ div[style*="gridTemplateColumns:1fr auto"]{ grid-template-columns:1fr !important; } }`}</style>
    </div>
  )
}
