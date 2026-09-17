import React, { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiGet, apiPost, apiDelete, normalizeApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import { formatPrice, formatDate, nightsBetween, todayISO } from '../lib/format'
import { ROOM_TYPES } from '../lib/constants'
import Spinner from '../components/Spinner'
import Alert from '../components/Alert'
import Badge from '../components/Badge'
import StarRating from '../components/StarRating'
import FavoriteButton from '../components/FavoriteButton'
import Button from '../components/Button'

function resolveHotelImage(images, fallback) {
  if (!images || images.length===0) return fallback
  const primary = images.find(i=>i.is_primary) || images[0]
  return primary.image || primary.url || fallback
}

export default function HotelDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { isAuthenticated } = useAuth()

  const [hotel, setHotel] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [amenitiesMap, setAmenitiesMap] = useState({})
  const [reviews, setReviews] = useState({ results:[], count:0 })
  const [reviewsPage, setReviewsPage] = useState(1)
  const [reviewsLoading, setReviewsLoading] = useState(false)

  // availability
  const [checkIn, setCheckIn] = useState(todayISO())
  const [checkOut, setCheckOut] = useState(()=>{ const d=new Date(); d.setDate(d.getDate()+1); return d.toISOString().split('T')[0] })
  const [guests, setGuests] = useState(2)
  const [rooms, setRooms] = useState([])
  const [roomsLoading, setRoomsLoading] = useState(false)
  const [roomsError, setRoomsError] = useState('')

  // favorite
  const [favoriteId, setFavoriteId] = useState(null)
  const [favLoading, setFavLoading] = useState(false)

  const fetchHotel = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const data = await apiGet(`/hotels/${id}/`)
      setHotel(data)
    } catch(e){
      const {message}=normalizeApiError(e); setError(message)
    } finally { setLoading(false)}
  }, [id])

  const fetchAmenities = useCallback(async ()=>{
    try{
      const data = await apiGet('/amenities/')
      const map={}
      const list = Array.isArray(data) ? data : (data.results || [])
      list.forEach(a=> map[a.id]=a.name)
      setAmenitiesMap(map)
    }catch{}
  },[])

  const fetchReviews = useCallback(async (page=1)=>{
    setReviewsLoading(true)
    try{
      const data = await apiGet('/reviews/', { hotel:id, page })
      setReviews(data)
      setReviewsPage(page)
    }catch{} finally{ setReviewsLoading(false)}
  },[id])

  const fetchRooms = useCallback(async ()=>{
    if(!hotel) return
    setRoomsLoading(true); setRoomsError('')
    // if dates provided, query rooms availability endpoint
    try{
      if(checkIn && checkOut){
        const data = await apiGet('/rooms/', { hotel:id, check_in: checkIn, check_out: checkOut })
        const list = Array.isArray(data) ? data : (data.results || data)
        setRooms(list)
      } else {
        setRooms(hotel.rooms || [])
      }
    }catch(e){
      const {message}=normalizeApiError(e)
      setRoomsError(message)
      setRooms(hotel.rooms || [])
    } finally{ setRoomsLoading(false)}
  },[hotel, id, checkIn, checkOut])

  const fetchFavorite = useCallback(async ()=>{
    if(!isAuthenticated) return
    try{
      const data = await apiGet('/favorites/')
      const list = Array.isArray(data) ? data : (data.results || [])
      const found = list.find(f=> String(f.hotel.id)===String(id) || String(f.hotel_id)===String(id))
      setFavoriteId(found ? found.id : null)
    }catch{}
  },[isAuthenticated, id])

  useEffect(()=>{ fetchHotel(); fetchAmenities(); fetchReviews(1); },[fetchHotel, fetchAmenities, fetchReviews])
  useEffect(()=>{ if(hotel) fetchRooms() },[fetchRooms])
  useEffect(()=>{ fetchFavorite() },[fetchFavorite])

  const handleFavoriteToggle = async()=>{
    if(!isAuthenticated){ navigate('/connexion', { state:{ from:`/hotels/${id}` } }); return }
    setFavLoading(true)
    try{
      if(favoriteId){
        await apiDelete(`/favorites/${favoriteId}/`)
        setFavoriteId(null)
      } else {
        const res = await apiPost('/favorites/', { hotel_id: Number(id) })
        setFavoriteId(res.id)
      }
    }catch(e){ /* ignore */ } finally{ setFavLoading(false)}
  }

  if(loading) return <div className="container page" style={{ display:'flex', justifyContent:'center', padding:'60px 0' }}><Spinner size="lg" /></div>
  if(error) return <div className="container page"><Alert type="error">{error}</Alert><div style={{ marginTop:12 }}><Link to="/" className="btn btn-secondary">Retour à l'accueil</Link></div></div>
  if(!hotel) return null

  const mainImg = resolveHotelImage(hotel.images, null)
  const sideImgs = (hotel.images || []).slice(1,5)
  const avg = hotel.average_rating
  const nights = nightsBetween(checkIn, checkOut)

  return (
    <div className="page hotel-detail-page">
      <div className="hotel-detail-media" aria-hidden="true">
        <img src="/images/bg-suite.jpg" alt="" role="presentation" className="hotel-detail-photo" loading="lazy" />
        <div className="hotel-detail-veil" aria-hidden="true" />
      </div>
      <div className="container" style={{ position:'relative', zIndex:1 }}>
        <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom:14, flexWrap:'wrap' }}>
          <Link to="/" className="small muted" style={{ textDecoration:'underline', textUnderlineOffset:3 }}>Accueil</Link>
          <span className="small muted">/</span>
          <span className="small" style={{ fontWeight:600 }}>{hotel.name}</span>
        </div>

        <div className="page-header" style={{ marginBottom:18 }}>
          <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', gap:16, flexWrap:'wrap' }}>
            <div>
              <p className="eyebrow">{hotel.city} · {hotel.country} · {hotel.stars} étoile{hotel.stars>1?'s':''}</p>
              <h1 style={{ marginTop:4 }}>{hotel.name}</h1>
              <p style={{ marginTop:8, display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
                <span className="badge badge-neutral">{hotel.stars} ★</span>
                {avg ? <><StarRating value={Number(avg)} size="sm" showValue /> <span className="small muted">({hotel.reviews_count} avis)</span></> : <span className="small muted">Nouveau — pas encore d'avis</span>}
                <span className="small muted">·</span>
                <span className="small muted">{hotel.address}</span>
              </p>
            </div>
            {isAuthenticated && (
              <div style={{ display:'flex', alignItems:'center', gap:8 }}>
                <FavoriteButton isFavorite={!!favoriteId} onToggle={handleFavoriteToggle} disabled={favLoading} size="md" />
                <span className="small muted">{favoriteId ? 'Dans vos favoris' : 'Ajouter aux favoris'}</span>
              </div>
            )}
          </div>
        </div>

        {/* Gallery */}
        <div className="gallery">
          <div className="gallery-main">
            {mainImg ? <img src={mainImg} alt={hotel.name} onError={(e)=>{e.currentTarget.style.display='none'}} /> : <div style={{ width:'100%', height:'100%', display:'grid', placeItems:'center', color:'var(--color-text-muted)', background:'rgba(255,255,255,0.04)', border:'1px dashed var(--color-border)' }}>Aucune image</div>}
          </div>
          <div className="gallery-side">
            {[0,1].map(i=>{
              const img = sideImgs[i]
              const url = img ? (img.image || img.url) : null
              return (
                <div key={i} style={{ borderRadius: i===0 ? '0 14px 0 0' : '0 0 14px 0' }}>
                  {url ? <img src={url} alt="" onError={(e)=>{e.currentTarget.style.display='none'}} /> : <div style={{ width:'100%', height:'100%', display:'grid', placeItems:'center', background:'rgba(255,255,255,0.04)', color:'var(--color-text-muted)', fontSize:'0.85rem' }}>—</div>}
                </div>
              )
            })}
          </div>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'1.7fr 0.9fr', gap:24, marginTop:24 }}>
          <div style={{ display:'flex', flexDirection:'column', gap:18 }}>
            <div className="card">
              <div className="card-body">
                <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.2rem', marginBottom:8 }}>À propos</h2>
                <p className="muted" style={{ lineHeight:1.7, whiteSpace:'pre-wrap' }}>{hotel.description || 'Cet établissement n\'a pas encore renseigné de description. Profitez d\'un cadre soigné et d\'un accueil attentionné pour votre séjour.'}</p>
                {hotel.amenities && hotel.amenities.length>0 && (
                  <div style={{ marginTop:14 }}>
                    <h3 className="small" style={{ fontWeight:700, marginBottom:8 }}>Équipements</h3>
                    <div className="amenity-chips">
                      {hotel.amenities.map(aid=> (
                        <span key={aid} className="chip">{amenitiesMap[aid] || `Équipement #${aid}`}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="card">
              <div className="card-body">
                <div style={{ display:'flex', alignItems:'baseline', justifyContent:'space-between', gap:12, marginBottom:12 }}>
                  <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.2rem' }}>Avis des voyageurs</h2>
                  {avg && <span className="badge badge-warning">{Number(avg).toFixed(1)} / 5 · {hotel.reviews_count} avis</span>}
                </div>
                {reviewsLoading ? <div style={{ display:'flex', justifyContent:'center', padding:20 }}><Spinner /></div> : reviews.results.length===0 ? (
                  <p className="small muted">Aucun avis pour le moment.</p>
                ) : (
                  <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                    {reviews.results.map(r=>(
                      <div key={r.id} style={{ padding:'14px 0', borderBottom:'1px solid var(--color-border)' }}>
                        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', gap:12 }}>
                          <strong style={{ fontSize:'0.92rem' }}>{r.user}</strong>
                          <StarRating value={r.rating} size="sm" />
                        </div>
                        {r.comment && <p className="small" style={{ marginTop:6, lineHeight:1.6, color:'var(--color-text-secondary)' }}>{r.comment}</p>}
                        <p className="small muted" style={{ marginTop:6, fontSize:'0.78rem' }}>{formatDate(r.created_at)}</p>
                      </div>
                    ))}
                    {reviews.count > reviews.results.length && (
                      <div style={{ display:'flex', gap:8, marginTop:6 }}>
                        <Button variant="secondary" size="sm" onClick={()=>fetchReviews(reviewsPage+1)}>Charger plus d'avis</Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
            <div className="card summary-card" style={{ position:'static' }}>
              <div className="card-body">
                <h3 style={{ fontFamily:'var(--font-display)', fontSize:'1.05rem', marginBottom:12 }}>Vérifier la disponibilité</h3>
                <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10 }}>
                  <div className="field"><label className="field-label" htmlFor="ci">Arrivée</label><input id="ci" className="field-input" type="date" value={checkIn} onChange={e=>setCheckIn(e.target.value)} /></div>
                  <div className="field"><label className="field-label" htmlFor="co">Départ</label><input id="co" className="field-input" type="date" value={checkOut} onChange={e=>setCheckOut(e.target.value)} /></div>
                </div>
                <div className="field" style={{ marginTop:10 }}>
                  <label className="field-label" htmlFor="guests">Voyageurs</label>
                  <select id="guests" className="field-input" value={guests} onChange={e=>setGuests(Number(e.target.value))}>
                    {[1,2,3,4,5,6].map(n=><option key={n} value={n}>{n} voyageur{n>1?'s':''}</option>)}
                  </select>
                </div>
                {nights>0 && <p className="small muted" style={{ marginTop:8 }}>{nights} nuit{nights>1?'s':''} · du {formatDate(checkIn)} au {formatDate(checkOut)}</p>}
                <Button variant="secondary" size="sm" onClick={fetchRooms} style={{ marginTop:10 }} loading={roomsLoading}>Actualiser les chambres</Button>
              </div>
            </div>

            <div>
              <h3 style={{ fontFamily:'var(--font-display)', fontSize:'1.05rem', marginBottom:10 }}>Chambres</h3>
              {roomsError && <Alert type="error" style={{ marginBottom:10 }}>{roomsError}</Alert>}
              {roomsLoading ? <div style={{ display:'flex', justifyContent:'center', padding:20 }}><Spinner /></div> : rooms.length===0 ? (
                <div className="card"><div className="card-body"><p className="small muted">Aucune chambre disponible pour ces dates. Essayez d'autres dates ou contactez l'établissement.</p></div></div>
              ) : (
                <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
                  {rooms.map(room=>{
                    const img = room.images && room.images[0] ? (room.images[0].image || room.images[0].url) : null
                    const typeLabel = room.room_type_display || ROOM_TYPES[room.room_type] || room.room_type
                    const amenityNames = (room.amenities || []).map(id=> amenitiesMap[id] || `#${id}`)
                    return (
                      <div key={room.id} className="room-card">
                        <div className="room-card-media">
                          {img ? <img src={img} alt="" onError={e=>{e.currentTarget.style.display='none'}} /> : <div style={{ width:'100%', height:'100%', display:'grid', placeItems:'center', background:'rgba(255,255,255,0.04)', color:'var(--color-text-muted)', fontSize:'0.85rem' }}>Aucune image</div>}
                          {!room.is_available && <span style={{ position:'absolute', top:10, left:10 }} className="badge badge-neutral">Indisponible</span>}
                        </div>
                        <div className="room-card-body">
                          <div style={{ display:'flex', justifyContent:'space-between', gap:12, alignItems:'flex-start' }}>
                            <div>
                              <div className="room-type">{typeLabel} — {room.room_number}</div>
                              <div className="small muted">{room.max_occupancy} pers. max · {room.beds} lit{room.beds>1?'s':''}</div>
                            </div>
                            <div style={{ textAlign:'right' }}>
                              <div className="price">{formatPrice(room.price_per_night)} <small>/ nuit</small></div>
                            </div>
                          </div>
                          {room.description && <p className="small muted" style={{ lineHeight:1.6 }}>{room.description}</p>}
                          {amenityNames.length>0 && (
                            <div className="amenity-chips">
                              {amenityNames.map((n,i)=><span key={i} className="chip" style={{ fontSize:'0.75rem' }}>{n}</span>)}
                            </div>
                          )}
                          <div style={{ marginTop:8 }}>
                            {isAuthenticated ? (
                              <Button
                                as="a"
                                href={`/reservation?hotel=${hotel.id}&room=${room.id}&check_in=${checkIn}&check_out=${checkOut}`}
                                onClick={(e)=>{ e.preventDefault(); navigate(`/reservation?hotel=${hotel.id}&room=${room.id}&check_in=${checkIn}&check_out=${checkOut}`)}}
                                disabled={!room.is_available}
                              >
                                Réserver
                              </Button>
                            ) : (
                              <Button onClick={()=> navigate('/connexion', { state:{ from: `/hotels/${id}` } })} variant="secondary">Se connecter pour réserver</Button>
                            )}
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      <style>{`@media(max-width: 900px){ div[style*="gridTemplateColumns:1.7fr"]{ grid-template-columns:1fr !important; } }`}</style>
    </div>
  )
}
