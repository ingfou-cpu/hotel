// HotelCard.jsx — Carte d'hôtel pour listes
import React from 'react'
import { Link } from 'react-router-dom'
import { formatPrice } from '../lib/format'
import StarRating from './StarRating'

function resolveImage(hotel) {
  if (hotel.image) return hotel.image
  if (hotel.images && hotel.images[0]) {
    const first = hotel.images[0]
    if (typeof first === 'string') return first
    return first.image || first.url || null
  }
  return null
}

export default function HotelCard({ hotel, className = '' }) {
  const imageUrl = resolveImage(hotel)
  const stars = hotel.stars || 0
  const rating = hotel.average_rating ?? hotel.rating ?? null
  const reviews = hotel.reviews_count ?? 0
  const price = hotel.starting_price ?? hotel.startingPrice ?? null

  return (
    <article className={`card hotel-card ${className}`}>
      <Link to={`/hotels/${hotel.id}`} className="hotel-card-media" aria-label={`Voir ${hotel.name}`}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt=""
            loading="lazy"
            onError={(e) => { e.currentTarget.style.display = 'none'; e.currentTarget.nextSibling && (e.currentTarget.nextSibling.style.display = 'grid') }}
          />
        ) : null}
        <div style={{ display: imageUrl ? 'none' : 'grid', placeItems:'center', width:'100%', height:'100%', background:'rgba(255,255,255,0.04)', color:'var(--color-text-muted)', fontSize:'0.9rem', fontWeight:600, border:'1px dashed var(--color-border)' }}>
          Aucune image
        </div>
        {stars > 0 && (
          <span className="hotel-card-badge">
            <span aria-hidden="true">★</span> {stars} étoile{stars>1?'s':''}
          </span>
        )}
        {rating ? (
          <span style={{ position:'absolute', top:12, right:12, background:'rgba(14,11,9,0.82)', color:'#fff', borderRadius:9999, padding:'6px 10px', fontSize:'0.8rem', fontWeight:700, display:'flex', alignItems:'center', gap:6, border:'1px solid rgba(255,255,255,0.12)', backdropFilter:'blur(8px)' }}>
            <span aria-hidden="true" style={{ color:'var(--color-accent)' }}>◆</span> {Number(rating).toFixed(1)}
          </span>
        ) : null}
      </Link>
      <div className="hotel-card-body">
        <Link to={`/hotels/${hotel.id}`} style={{ textDecoration:'none', color:'inherit' }}>
          <h3 className="hotel-card-title">{hotel.name}</h3>
        </Link>
        <p className="hotel-card-meta">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true"><path d="M7 12.5C7 12.5 11 9 11 6.5a4 4 0 0 0-8 0c0 2.5 4 6 4 6z" stroke="currentColor" strokeWidth="1.2"/><circle cx="7" cy="6.5" r="1.5" stroke="currentColor" strokeWidth="1.2"/></svg>
          {hotel.city}{hotel.country ? `, ${hotel.country}` : ''}
        </p>
        <div className="hotel-card-footer">
          <div>
            {rating ? (
              <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                <StarRating value={Number(rating)} size="sm" />
                <span className="small muted">({reviews} avis)</span>
              </div>
            ) : (
              <span className="small muted">{reviews ? `${reviews} avis` : 'Nouveau'}</span>
            )}
          </div>
          {price && (
            <div style={{ textAlign:'right' }}>
              <div className="price">{formatPrice(price)} <small>/ nuit</small></div>
              <div className="small muted" style={{ fontSize:'0.74rem' }}>à partir de</div>
            </div>
          )}
        </div>
      </div>
    </article>
  )
}
