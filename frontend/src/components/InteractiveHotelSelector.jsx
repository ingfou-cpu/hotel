// InteractiveHotelSelector.jsx — adaptation 21st.dev #2541 "Interactive Selector" (minhxthanh) pour les hôtels
// Mécaniques conservées : flex row height ~400px, flex active 7 / inactive 1, transition 700ms,
// backgroundSize auto 100% / 120%, inset shadow, chip 44px, stagger translateX -60px 180*index, header translateY.
// Contenu réécrit pour hôtels : image, nom, ville/pays, étoiles, avis, prix (formatPrice, FR).
import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { formatPrice } from '../lib/format'

function resolveImage(hotel) {
  if (hotel.image) return hotel.image
  if (hotel.images && hotel.images[0]) {
    const first = hotel.images[0]
    if (typeof first === 'string') return first
    return first.image || first.url || null
  }
  return null
}

export default function InteractiveHotelSelector({ hotels = [] }) {
  const navigate = useNavigate()
  const [active, setActive] = useState(0)
  const [visible, setVisible] = useState([])
  const timeoutsRef = useRef([])

  // reset active + stagger when page results change
  useEffect(() => {
    setActive(0)
    setVisible([])
    timeoutsRef.current.forEach(clearTimeout)
    timeoutsRef.current = []
    hotels.forEach((_, i) => {
      const t = setTimeout(() => {
        setVisible((prev) => (prev.includes(i) ? prev : [...prev, i]))
      }, 180 * i)
      timeoutsRef.current.push(t)
    })
    return () => timeoutsRef.current.forEach(clearTimeout)
  }, [hotels])

  if (!hotels.length) return null

  const handleSelect = (idx, hotel) => {
    if (idx === active) {
      navigate(`/hotels/${hotel.id}`)
    } else {
      setActive(idx)
    }
  }

  const handleKeyDown = (e, idx, hotel) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleSelect(idx, hotel)
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      setActive((prev) => Math.min(hotels.length - 1, prev + 1))
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      setActive((prev) => Math.max(0, prev - 1))
    }
  }

  return (
    <div className="interactive-selector-wrap">
      <div
        className="interactive-selector"
        role="list"
        aria-label="Sélection d'hôtels — cliquez pour agrandir, recliquez pour voir l'hôtel"
      >
        {hotels.map((hotel, idx) => {
          const isActive = idx === active
          const isVisible = visible.includes(idx)
          const imageUrl = resolveImage(hotel)
          const stars = hotel.stars || 0
          const rating = hotel.average_rating ?? hotel.rating ?? null
          const reviews = hotel.reviews_count ?? 0
          const price = hotel.starting_price ?? hotel.startingPrice ?? null
          const cityCountry = [hotel.city, hotel.country].filter(Boolean).join(', ')

          return (
            <div
              key={hotel.id}
              role="listitem"
              tabIndex={0}
              aria-selected={isActive}
              aria-label={`${hotel.name}, ${cityCountry}${stars ? `, ${stars} étoiles` : ''} — ${isActive ? 'sélectionné, appuyez pour voir' : 'appuyez pour agrandir'}`}
              className={`interactive-selector__option ${isActive ? 'is-active' : ''} ${isVisible ? 'is-visible' : ''}`}
              onClick={() => handleSelect(idx, hotel)}
              onKeyDown={(e) => handleKeyDown(e, idx, hotel)}
              style={
                imageUrl
                  ? {
                      backgroundImage: `url("${imageUrl}")`,
                    }
                  : undefined
              }
            >
              {/* image fallback when no url */}
              {!imageUrl && <div className="interactive-selector__fallback" aria-hidden="true" />}

              {/* inset shadow gradient for legibility */}
              <div className="interactive-selector__veil" aria-hidden="true" />
              <div className="interactive-selector__shade" aria-hidden="true" />

              {/* bottom label row */}
              <div className="interactive-selector__bottom">
                <span className="interactive-selector__chip" aria-hidden="true">
                  {/* building / hotel icon */}
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M3 21V7a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v14" />
                    <path d="M14 21V11a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10" />
                    <path d="M3 21h18" />
                    <path d="M7 10h2M7 13h2M7 16h2M16 14h2M16 17h2" />
                  </svg>
                </span>

                <div className="interactive-selector__text">
                  <h3 className="interactive-selector__title">{hotel.name}</h3>
                  <p className="interactive-selector__subtitle">
                    <span className="interactive-selector__loc">
                      <svg width="12" height="12" viewBox="0 0 14 14" fill="none" aria-hidden="true" style={{ flexShrink: 0 }}>
                        <path d="M7 12.5C7 12.5 11 9 11 6.5a4 4 0 0 0-8 0c0 2.5 4 6 4 6z" stroke="currentColor" strokeWidth="1.2" />
                        <circle cx="7" cy="6.5" r="1.5" stroke="currentColor" strokeWidth="1.2" />
                      </svg>
                      {cityCountry || 'Adresse confidentielle'}
                    </span>
                    {stars > 0 && (
                      <>
                        <span className="interactive-selector__dot" aria-hidden="true">·</span>
                        <span>{stars} étoile{stars > 1 ? 's' : ''}</span>
                      </>
                    )}
                    {rating != null && (
                      <>
                        <span className="interactive-selector__dot" aria-hidden="true">·</span>
                        <span className="interactive-selector__rating">
                          <svg width="10" height="10" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true" style={{ color: 'var(--color-accent)' }}>
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                          {Number(rating).toFixed(1)}
                        </span>
                        <span className="small">({reviews} avis)</span>
                      </>
                    )}
                    {!rating && reviews === 0 && stars === 0 && <><span className="interactive-selector__dot">·</span><span>Nouveau</span></>}
                  </p>

                  {/* price + CTA only when active — reveals with same translate */}
                  <div className="interactive-selector__meta">
                    {price != null && price !== '' ? (
                      <span className="interactive-selector__price">
                        <span className="interactive-selector__price-label">à partir de</span>
                        <span className="interactive-selector__price-value">{formatPrice(price)} <small>/ nuit</small></span>
                      </span>
                    ) : (
                      <span className="small" style={{ color: 'rgba(255,255,255,0.72)' }}>Disponibilités à consulter</span>
                    )}
                    <Link
                      to={`/hotels/${hotel.id}`}
                      className="btn btn-primary btn-sm interactive-selector__cta"
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`Voir ${hotel.name}`}
                    >
                      Voir l'hôtel
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                        <path d="M5 3l4 4-4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                    </Link>
                  </div>
                </div>
              </div>

              {/* subtle top hint when collapsed — hotel name vertical fallback for discoverability */}
              {!isActive && (
                <span className="interactive-selector__collapsed-label" aria-hidden="true">
                  {hotel.name}
                </span>
              )}
            </div>
          )
        })}
      </div>

      {/* helper caption — like demo subtitle but for hotels */}
      <p className="interactive-selector__hint">
        <span className="interactive-selector__hint-dot" aria-hidden="true" />
        Cliquez sur une carte pour agrandir — cliquez à nouveau ou sur « Voir l'hôtel » pour découvrir
      </p>
    </div>
  )
}
