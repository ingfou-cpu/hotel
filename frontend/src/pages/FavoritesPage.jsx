import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiGet, apiDelete, normalizeApiError } from '../lib/api'
import Alert from '../components/Alert'
import Spinner from '../components/Spinner'
import EmptyState from '../components/EmptyState'
import Button from '../components/Button'

export default function FavoritesPage(){
  const [favorites, setFavorites] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(null)

  const fetchFav = async()=>{
    setLoading(true); setError('')
    try{
      const data = await apiGet('/favorites/')
      const list = Array.isArray(data) ? data : (data.results || [])
      setFavorites(list)
    }catch(e){
      const {message}=normalizeApiError(e); setError(message)
    } finally{ setLoading(false)}
  }
  useEffect(()=>{ fetchFav() },[])

  const handleRemove = async(fav)=>{
    setBusy(fav.id)
    try{
      await apiDelete(`/favorites/${fav.id}/`)
      setFavorites(prev=> prev.filter(f=> f.id!==fav.id))
    }catch(e){
      const {message}=normalizeApiError(e); setError(message)
    } finally{ setBusy(null)}
  }

  if(loading) return <div className="container page" style={{ display:'flex', justifyContent:'center', padding:40 }}><Spinner size="lg" /></div>

  return (
    <div className="container page">
      <div className="page-header">
        <p className="eyebrow">Votre sélection</p>
        <h1>Favoris</h1>
        <p>Retrouvez vos hôtels enregistrés et accédez rapidement à leurs disponibilités.</p>
      </div>

      {error && <div style={{ marginBottom:12 }}><Alert type="error">{error}</Alert></div>}

      {favorites.length===0 ? (
        <EmptyState
          title="Aucun favori"
          description="Parcourez nos hôtels et ajoutez vos coups de cœur à vos favoris pour les retrouver ici."
          action={<Link to="/" className="btn btn-primary">Découvrir les hôtels</Link>}
        />
      ) : (
        <div className="grid grid-hotels">
          {favorites.map(fav=>{
            const h = fav.hotel
            const img = h.image
            return (
              <article key={fav.id} className="card hotel-card">
                <Link to={`/hotels/${h.id}`} className="hotel-card-media" aria-label={h.name}>
                  {img ? <img src={img} alt="" loading="lazy" onError={e=>{e.currentTarget.style.display='none'}} /> : <div style={{ width:'100%', height:'100%', display:'grid', placeItems:'center', background:'rgba(255,255,255,0.04)', color:'var(--color-text-muted)', border:'1px dashed var(--color-border)' }}>Aucune image</div>}
                </Link>
                <div className="hotel-card-body">
                  <Link to={`/hotels/${h.id}`} style={{ textDecoration:'none', color:'inherit' }}>
                    <h3 className="hotel-card-title">{h.name}</h3>
                  </Link>
                  <p className="hotel-card-meta">{h.city}, {h.country}</p>
                  <div style={{ display:'flex', justifyContent:'space-between', gap:8, marginTop:10, alignItems:'center' }}>
                    <Link to={`/hotels/${h.id}`} className="btn btn-secondary btn-sm">Voir l'hôtel</Link>
                    <Button variant="ghost" size="sm" loading={busy===fav.id} onClick={()=> handleRemove(fav)}>Retirer</Button>
                  </div>
                </div>
              </article>
            )
          })}
        </div>
      )}
    </div>
  )
}
