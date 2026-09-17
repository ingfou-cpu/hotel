import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiGet, apiPost, normalizeApiError } from '../lib/api'
import { formatDateTime } from '../lib/format'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import EmptyState from '../components/EmptyState'
import Badge from '../components/Badge'
import Button from '../components/Button'

const typeColor = {
  info:'info',
  booking:'success',
  payment:'warning',
  cancellation:'danger',
  reminder:'info'
}

export default function NotificationsPage(){
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [marking, setMarking] = useState(false)

  const fetchData = async()=>{
    setLoading(true); setError('')
    try{
      const data = await apiGet('/notifications/')
      const list = Array.isArray(data) ? data : (data.results || [])
      setItems(list)
    }catch(e){
      const {message}=normalizeApiError(e); setError(message)
    } finally{ setLoading(false)}
  }
  useEffect(()=>{ fetchData() },[])

  const markOne = async(n)=>{
    if(n.is_read) return
    try{
      await apiPost(`/notifications/${n.id}/read/`, {})
      setItems(prev=> prev.map(x=> x.id===n.id ? {...x, is_read:true} : x))
    }catch{}
  }
  const markAll = async()=>{
    setMarking(true)
    try{
      await apiPost('/notifications/mark_all_read/', {})
      setItems(prev=> prev.map(x=> ({...x, is_read:true})))
    }catch(e){
      const {message}=normalizeApiError(e); setError(message)
    } finally{ setMarking(false)}
  }

  if(loading) return <div className="container page" style={{ display:'flex', justifyContent:'center', padding:40 }}><Spinner size="lg" /></div>

  return (
    <div className="container page" style={{ maxWidth:820 }}>
      <div className="page-header">
        <div style={{ display:'flex', alignItems:'flex-end', justifyContent:'space-between', gap:12, flexWrap:'wrap' }}>
          <div>
            <p className="eyebrow">Centre de notifications</p>
            <h1>Notifications</h1>
            <p>Confirmations, paiements, annulations et rappels de séjour.</p>
          </div>
          {items.some(i=>!i.is_read) && <Button variant="secondary" size="sm" loading={marking} onClick={markAll}>Tout marquer comme lu</Button>}
        </div>
      </div>

      {error && <div style={{ marginBottom:12 }}><Alert type="error">{error}</Alert></div>}

      {items.length===0 ? (
        <EmptyState title="Aucune notification" description="Vous serez notifié ici lors de vos réservations, paiements et rappels de séjour." />
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          {items.map(n=>{
            const isLink = n.link && n.link.startsWith('/')
            const Wrapper = isLink ? Link : 'div'
            const wrapperProps = isLink ? { to: n.link } : {}
            return (
              <div
                key={n.id}
                className={`notif-item ${!n.is_read ? 'unread' : ''}`}
                onClick={()=> markOne(n)}
                role={isLink ? undefined : 'button'}
                tabIndex={0}
                onKeyDown={(e)=>{ if(e.key==='Enter') markOne(n)}}
                style={{ cursor:'pointer' }}
              >
                <div style={{ width:10, height:10, borderRadius:'50%', background: !n.is_read ? 'var(--color-accent)' : 'transparent', border: !n.is_read ? 'none' : '1px solid var(--color-border)', marginTop:6, flexShrink:0 }} />
                <div style={{ flex:1 }}>
                  <div style={{ display:'flex', alignItems:'center', gap:8, flexWrap:'wrap' }}>
                    <Badge color={typeColor[n.type] || 'neutral'}>{n.type}</Badge>
                    <span style={{ fontWeight:700, fontSize:'0.95rem' }}>{n.title}</span>
                    {!n.is_read && <span className="badge badge-info" style={{ fontSize:'0.7rem' }}>Nouveau</span>}
                  </div>
                  <p className="small" style={{ marginTop:6, lineHeight:1.6, color:'var(--color-text-secondary)' }}>{n.message}</p>
                  <div style={{ display:'flex', alignItems:'center', gap:8, marginTop:8, flexWrap:'wrap' }}>
                    <span className="small muted" style={{ fontSize:'0.78rem' }}>{formatDateTime(n.created_at)}</span>
                    {n.link && isLink && <Link to={n.link} onClick={e=>e.stopPropagation()} className="small" style={{ fontWeight:700, textDecoration:'underline', textUnderlineOffset:3 }}>Ouvrir</Link>}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
