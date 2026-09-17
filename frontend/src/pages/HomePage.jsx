import React, { useEffect, useState, useCallback, useRef } from 'react'
import { useSearchParams, Link, useLocation } from 'react-router-dom'
import { motion } from 'motion/react'
import { apiGet, normalizeApiError } from '../lib/api'
import InteractiveHotelSelector from '../components/InteractiveHotelSelector'
import Spinner from '../components/Spinner'
import Alert from '../components/Alert'
import EmptyState from '../components/EmptyState'
import Pagination from '../components/Pagination'
import Button from '../components/Button'
import FadingVideo from '../components/FadingVideo'
import BlurText from '../components/BlurText'
import StackSpread from '../components/ui/stack-spread'

const PAGE_SIZE = 20

function useFilters(searchParams) {
  return {
    search: searchParams.get('search') || '',
    city: searchParams.get('city') || '',
    country: searchParams.get('country') || '',
    stars: searchParams.get('stars') || '',
    guests: searchParams.get('guests') || '',
    check_in: searchParams.get('check_in') || '',
    check_out: searchParams.get('check_out') || '',
    sort: searchParams.get('sort') || '',
    ordering: searchParams.get('ordering') || '',
    page: parseInt(searchParams.get('page') || '1', 10) || 1,
  }
}

export default function HomePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const location = useLocation()
  const filters = useFilters(searchParams)

  // Scroll to anchored sections when hash present — handles À propos, Destinations, Avis, Hébergements etc.
  useEffect(() => {
    if (location.hash) {
      const id = location.hash.slice(1)
      const el = document.getElementById(id)
      if (el) requestAnimationFrame(() => el.scrollIntoView({ behavior: 'smooth', block: 'start' }))
    }
  }, [location])

  // Robust re-click handling: hashchange + initial hash on mount (generic for all anchors)
  useEffect(() => {
    const onHashChange = () => {
      const hash = window.location.hash
      if (hash) document.getElementById(hash.slice(1))?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
    window.addEventListener('hashchange', onHashChange)
    if (window.location.hash) setTimeout(onHashChange, 80)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  // local form state mirrors filters for controlled inputs
  const [form, setForm] = useState({
    search: filters.search,
    city: filters.city,
    country: filters.country,
    stars: filters.stars,
    guests: filters.guests,
    check_in: filters.check_in,
    check_out: filters.check_out,
    sort: filters.sort,
  })

  useEffect(() => {
    setForm({
      search: filters.search,
      city: filters.city,
      country: filters.country,
      stars: filters.stars,
      guests: filters.guests,
      check_in: filters.check_in,
      check_out: filters.check_out,
      sort: filters.sort,
    })
  }, [searchParams])

  const [data, setData] = useState({ results: [], count: 0 })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [destinations, setDestinations] = useState([])

  const fetchHotels = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (filters.search) params.search = filters.search
      if (filters.city) params.city = filters.city
      if (filters.country) params.country = filters.country
      if (filters.stars) params.stars = filters.stars
      if (filters.guests) params.guests = filters.guests
      if (filters.check_in) params.check_in = filters.check_in
      if (filters.check_out) params.check_out = filters.check_out
      if (filters.sort) params.sort = filters.sort
      if (filters.ordering) params.ordering = filters.ordering
      params.page = filters.page
      const res = await apiGet('/hotels/', params)
      setData(res)
    } catch (e) {
      const { message } = normalizeApiError(e)
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [filters.search, filters.city, filters.country, filters.stars, filters.guests, filters.check_in, filters.check_out, filters.sort, filters.ordering, filters.page])

  useEffect(() => { fetchHotels() }, [fetchHotels])

  // Destinations band: derive unique (city, country) counts from real hotel data (no invented content)
  useEffect(() => {
    let cancelled = false
    async function loadDestinations() {
      try {
        const res = await apiGet('/hotels/', { page_size: 100 })
        const hotels = res.results || res || []
        const map = new Map()
        hotels.forEach((h) => {
          const city = (h.city || '').trim()
          const country = (h.country || '').trim()
          if (!city) return
          const key = `${city}__${country}`
          const entry = map.get(key)
          if (entry) entry.count += 1
          else map.set(key, { city, country, count: 1 })
        })
        const sorted = Array.from(map.values()).sort((a, b) => b.count - a.count || a.city.localeCompare(b.city)).slice(0, 5)
        if (!cancelled) setDestinations(sorted)
      } catch {
        if (!cancelled) setDestinations([])
      }
    }
    loadDestinations()
    return () => { cancelled = true }
  }, [])

  const updateParams = (patch, resetPage = false) => {
    const next = new URLSearchParams(searchParams)
    Object.entries(patch).forEach(([k, v]) => {
      if (v === '' || v == null) next.delete(k)
      else next.set(k, String(v))
    })
    if (resetPage) next.delete('page')
    // ensure page present if needed
    setSearchParams(next, { replace: false })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    updateParams({ ...form, page: 1 }, false)
    const next = new URLSearchParams()
    Object.entries(form).forEach(([k, v]) => { if (v) next.set(k, String(v)) })
    next.set('page', '1')
    // remove empty
    Object.entries(form).forEach(([k,v])=> { if(!v) next.delete(k)})
    setSearchParams(next)
  }

  const handleReset = () => {
    setForm({ search:'', city:'', country:'', stars:'', guests:'', check_in:'', check_out:'', sort:'' })
    setSearchParams(new URLSearchParams())
  }

  const pageCount = Math.max(1, Math.ceil((data.count || 0) / PAGE_SIZE))
  const currentPage = filters.page
  const hotels = data.results || []

  const heroVideoSrc = "https://d8j0ntlcm91z4.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/hf_20260901_122529_931c22c8-8d2d-47c0-ad51-b97f56a91e42.mp4"
  const heroPoster = "https://d2ol7oe51mr4n9.cloudfront.net/user_38xzZboKViGWJOttwIXH07lWA1P/4f690bd1-881a-4192-82f2-d714d34c8fb9.png"

  return (
    <div>
      <section className="hero" aria-labelledby="hero-title">
        <div className="hero-image-wrap" aria-hidden="true">
          <img src="/images/bg-hero.jpg" alt="" className="hero-image" loading="eager" fetchPriority="high" decoding="async" />
        </div>
        <div className="container hero-inner">
          <div style={{ maxWidth: 760 }}>
            <div className="hero-pill" role="status" aria-label="Collection mise en avant">
              <span className="hero-pill-badge">Nouveau</span>
              <span>Collection Hôtel Lumière — {data.count ? `${data.count} adresses d\u2019exception` : "Sélection d\u2019exception"}</span>
            </div>
            <BlurText
              text="Des séjours pensés pour durer."
              as="h1"
              italicWord="pensés"
              className="hero-title"
              style={{ fontFamily:'var(--font-display)', fontSize:'clamp(2.8rem,6vw,4.4rem)', lineHeight:0.92, letterSpacing:'-0.04em', fontWeight:400, color:'#fff', marginTop:18 }}
            />
            <p className="hero-sub">
              Hôtels de caractère, disponibilités en temps réel et confirmation en quelques minutes. Une collection courte, choisie pour son charme et son accueil — paiement sécurisé, assistance attentive.
            </p>
            <div style={{ marginTop:20, display:'flex', gap:12, flexWrap:'wrap', alignItems:'center' }}>
              <a href="#hebergements" className="btn btn-primary btn-lg" onClick={(e)=>{e.preventDefault(); document.getElementById('hebergements')?.scrollIntoView({behavior:'smooth', block:'start'})}}>Explorer les hébergements</a>
              <a href="#a-propos" className="btn btn-secondary btn-lg" onClick={(e)=>{e.preventDefault(); document.getElementById('a-propos')?.scrollIntoView({behavior:'smooth', block:'start'})}}>Découvrir la collection</a>
              <span className="small" style={{ color:'rgba(255,255,255,0.64)', fontWeight:600 }}>Annulation selon conditions · Paiement sécurisé</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="search-panel liquid-glass--strong" aria-label="Recherche d'hôtels" style={{ marginTop:26 }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
              <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.1rem' }}>Rechercher un séjour</h2>
              <button type="button" className="btn btn-ghost btn-sm" onClick={handleReset}>Réinitialiser</button>
            </div>

            <div className="search-panel-grid">
              <div className="field">
                <label className="field-label" htmlFor="search">Recherche</label>
                <input id="search" className="field-input" placeholder="Nom, adresse…" value={form.search} onChange={(e)=>setForm({...form, search:e.target.value})} />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="city">Ville</label>
                <input id="city" className="field-input" placeholder="Paris" value={form.city} onChange={(e)=>setForm({...form, city:e.target.value})} />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="country">Pays</label>
                <input id="country" className="field-input" placeholder="France" value={form.country} onChange={(e)=>setForm({...form, country:e.target.value})} />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="stars">Étoiles minimum</label>
                <select id="stars" className="field-input" value={form.stars} onChange={(e)=>setForm({...form, stars:e.target.value})}>
                  <option value="">Indifférent</option>
                  <option value="3">3 ★ et plus</option>
                  <option value="4">4 ★ et plus</option>
                  <option value="5">5 ★</option>
                </select>
              </div>
              <div className="field">
                <label className="field-label" htmlFor="guests">Voyageurs</label>
                <select id="guests" className="field-input" value={form.guests} onChange={(e)=>setForm({...form, guests:e.target.value})}>
                  <option value="">Indifférent</option>
                  <option value="1">1 voyageur</option>
                  <option value="2">2 voyageurs</option>
                  <option value="3">3 voyageurs</option>
                  <option value="4">4 voyageurs</option>
                </select>
              </div>
              <div className="field">
                <label className="field-label" htmlFor="sort">Trier par</label>
                <select id="sort" className="field-input" value={form.sort} onChange={(e)=>setForm({...form, sort:e.target.value})}>
                  <option value="">Pertinence</option>
                  <option value="price">Prix croissant</option>
                  <option value="-price">Prix décroissant</option>
                </select>
              </div>
            </div>

            <div className="search-panel-grid" style={{ gridTemplateColumns:'repeat(2,1fr)' }}>
              <div className="field">
                <label className="field-label" htmlFor="check_in">Arrivée</label>
                <input id="check_in" className="field-input" type="date" value={form.check_in} onChange={(e)=>setForm({...form, check_in:e.target.value})} />
              </div>
              <div className="field">
                <label className="field-label" htmlFor="check_out">Départ</label>
                <input id="check_out" className="field-input" type="date" value={form.check_out} onChange={(e)=>setForm({...form, check_out:e.target.value})} />
              </div>
            </div>

            <div className="search-actions">
              <Button type="submit" size="lg">Rechercher</Button>
              <span className="small muted">Les filtres s'appliquent à la liste ci-dessous et sont conservés dans l'URL.</span>
            </div>
          </form>
        </div>
      </section>

      <section id="hebergements" style={{ paddingTop: 28 }}>
        <div className="container page" style={{ paddingTop: 0, paddingBottom: 40 }}>
          {error && <div style={{ marginBottom:16 }}><Alert type="error">{error}</Alert></div>}

          {loading ? (
            <div style={{ display:'flex', justifyContent:'center', padding:'48px 0' }}>
              <Spinner size="lg" ariaLabel="Chargement des hôtels" />
            </div>
          ) : data.results.length === 0 ? (
            <EmptyState
              icon={<svg width="48" height="48" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 9l9-6 9 6v10a1 1 0 0 1-1 1h-4V13H8v7H4a1 1 0 0 1-1-1V9z" stroke="currentColor" strokeWidth="1.5"/><path d="M9 21V13h6v8" stroke="currentColor" strokeWidth="1.5"/></svg>}
              title="Aucun hôtel ne correspond à votre recherche"
              description="Essayez d'élargir les dates, de réduire le nombre d'étoiles ou de voyageurs, ou d'effacer les filtres."
              action={<Button variant="secondary" onClick={handleReset}>Effacer les filtres</Button>}
            />
          ) : (
            <>
              <div style={{ display:'flex', alignItems:'baseline', justifyContent:'space-between', gap:12, marginBottom:16, flexWrap:'wrap' }}>
                <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.35rem' }}>Hôtels disponibles</h2>
                <span className="small muted">{data.count} résultat{data.count>1?'s':''} — page {currentPage} sur {pageCount}</span>
              </div>
              <InteractiveHotelSelector hotels={hotels} />
              <Pagination page={currentPage} pageCount={pageCount} total={data.count} onChange={(p)=> updateParams({ page: p })} />
            </>
          )}
        </div>
        {/* Immersive scroll showcase — full-bleed, placed AFTER the hotel list so #hebergements remains immediately useful; */}
        {/* tuning: dark bg to match --color-bg, cream text, shorter scroll for booking rhythm, 16px radius matching --radius-md */}
        <StackSpread
          scrollLength={220}
          bgColor="#14100C"
          textColor="#F6EFE6"
          cardRadius={16}
          showScrollHint
        />
      </section>

      <section id="a-propos" className="about-section" aria-labelledby="about-heading">
        <div className="container about-inner">
          <div className="about-header">
            <p className="eyebrow">À propos</p>
            <h2 id="about-heading">Une sélection d'hôtels <em>de caractère</em></h2>
            <p className="about-intro">Hôtel Lumière rassemble des adresses choisies pour leur charme, leur emplacement et la qualité de leur accueil — une collection courte pour trouver le bon lieu sans détour.</p>
          </div>

          <div className="about-grid">
            <article className="about-card">
              <span className="about-icon" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="8.5" />
                  <path d="M12 8.5V12l3 2" />
                  <path d="M9 3.5h6" />
                </svg>
              </span>
              <h3>Disponibilités en temps réel</h3>
              <p>Chambres mises à jour en continu, réservation confirmée en quelques minutes.</p>
            </article>

            <article className="about-card">
              <span className="about-icon" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 3l7 4v5c0 4.2-3 7.3-7 8.5C8 19.3 5 16.2 5 12V7l7-4z" />
                  <path d="M9 12l2 2 4-4" />
                </svg>
              </span>
              <h3>Paiement sécurisé</h3>
              <p>Paiement par carte, données protégées, annulation selon conditions.</p>
            </article>

            <article className="about-card">
              <span className="about-icon" aria-hidden="true">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 13a8 8 0 0 1 16 0v3a2 2 0 0 1-2 2h-1v-3h1v-2a6 6 0 0 0-12 0v2h1v3H6a2 2 0 0 1-2-2v-3z" />
                  <path d="M10 18a2 2 0 0 0 4 0h-4z" />
                  <path d="M8 15h8" />
                </svg>
              </span>
              <h3>Assistance 7j/7</h3>
              <p>Une équipe attentive avant, pendant et après votre séjour.</p>
            </article>
          </div>

          <div className="about-foot">
            <span className="chip">Sélection vérifiée</span>
            <span className="chip">Hôtes engagés</span>
            <span className="small muted">Même attention pour chaque adresse — sans classement artificiel.</span>
          </div>
        </div>
        <div className="about-media" aria-hidden="true">
          <img src="/images/bg-about.jpg" alt="" className="about-image" loading="lazy" decoding="async" />
        </div>
      </section>

      {destinations.length > 0 && (
        <section id="destinations" className="destinations-section" aria-labelledby="destinations-heading">
          <div className="container">
            <div className="section-header">
              <p className="eyebrow">Destinations</p>
              <h2 id="destinations-heading">Où voyager cette saison</h2>
              <p className="section-intro">Une sélection d'hôtels dans des villes que nos équipes connaissent bien.</p>
            </div>
            <div className="destinations-grid">
              {destinations.map((d) => (
                <Link
                  key={`${d.city}__${d.country}`}
                  to={{ pathname: '/', search: `?city=${encodeURIComponent(d.city)}` }}
                  className="destination-card"
                  aria-label={`${d.city}, ${d.country} — ${d.count} ${d.count > 1 ? 'hébergements' : 'hébergement'}`}
                >
                  <span className="destination-city">{d.city}</span>
                  <span className="destination-country">{d.country}</span>
                  <span className="destination-count">{d.count} {d.count > 1 ? 'hébergements' : 'hébergement'}</span>
                </Link>
              ))}
            </div>
          </div>
          <div className="destinations-media" aria-hidden="true">
            <img src="/images/bg-pool.jpg" alt="" role="presentation" className="destinations-photo" loading="lazy" />
            <div className="destinations-aurora">
              <span className="aurora-blob aurora-blob--1" />
              <span className="aurora-blob aurora-blob--2" />
              <span className="aurora-blob aurora-blob--3" />
            </div>
            <div className="destinations-veil" aria-hidden="true" />
          </div>
        </section>
      )}

      <section id="comment-ca-marche" className="steps-section" aria-labelledby="steps-heading">
        <div className="container">
          <div className="section-header">
            <p className="eyebrow">Comment ça marche</p>
            <h2 id="steps-heading">Réserver en trois étapes</h2>
          </div>
          <div className="steps-grid">
            <article className="step-card">
              <span className="step-num" aria-hidden="true">01</span>
              <h3>Recherchez</h3>
              <p>Trouvez l'hébergement idéal grâce à nos filtres : ville, étoiles, dates.</p>
            </article>
            <article className="step-card">
              <span className="step-num" aria-hidden="true">02</span>
              <h3>Réservez</h3>
              <p>Choisissez votre chambre et confirmez en quelques clics, paiement sécurisé.</p>
            </article>
            <article className="step-card">
              <span className="step-num" aria-hidden="true">03</span>
              <h3>Profitez</h3>
              <p>Recevez votre confirmation et partez serein, assistance 7j/7.</p>
            </article>
          </div>
        </div>
        <div className="steps-media" aria-hidden="true">
          <img src="/images/bg-spa.jpg" alt="" role="presentation" className="steps-photo" loading="lazy" />
          <div className="steps-grain" aria-hidden="true" />
          <div className="steps-dust" aria-hidden="true">
            <span className="dust-dot" />
            <span className="dust-dot" />
            <span className="dust-dot" />
            <span className="dust-dot" />
            <span className="dust-dot" />
            <span className="dust-dot" />
          </div>
          <div className="steps-veil" aria-hidden="true" />
        </div>
      </section>

      <section id="avis" className="reviews-section" aria-labelledby="reviews-heading">
        <div className="container">
          <div className="section-header">
            <p className="eyebrow">Avis</p>
            <h2 id="reviews-heading">Ils ont voyagé avec nous</h2>
          </div>
          <div className="reviews-grid">
            <article className="review-card">
              <span className="review-quote" aria-hidden="true">“</span>
              <p className="review-text">Un séjour magnifique, un hôtel confortable et un accompagnement parfait du début à la fin.</p>
              <p className="review-author">Camille · Lyon</p>
            </article>
            <article className="review-card">
              <span className="review-quote" aria-hidden="true">“</span>
              <p className="review-text">La réservation en ligne a été simple et rapide, exactement comme promis.</p>
              <p className="review-author">Yassine · Casablanca</p>
            </article>
            <article className="review-card">
              <span className="review-quote" aria-hidden="true">“</span>
              <p className="review-text">Une équipe réactive, une chambre impeccable, nous reviendrons c'est certain.</p>
              <p className="review-author">Eleonora · Rome</p>
            </article>
          </div>
        </div>
        <div className="reviews-media" aria-hidden="true">
          <img src="/images/bg-dining.jpg" alt="" role="presentation" className="reviews-photo" loading="lazy" />
          <div className="reviews-orbs" aria-hidden="true">
            <span className="reviews-orb reviews-orb--1" />
            <span className="reviews-orb reviews-orb--2" />
            <span className="reviews-orb reviews-orb--3" />
          </div>
          <div className="reviews-veil" aria-hidden="true" />
        </div>
      </section>

      <section className="cta-section" aria-labelledby="cta-heading">
        <div className="container cta-inner">
          <div className="cta-panel">
            <h2 id="cta-heading">Prêt pour votre prochaine escapade ?</h2>
            <p className="cta-sub">Explorez notre sélection d'hôtels choisis avec soin.</p>
            <a
              href="#hebergements"
              className="btn btn-primary btn-lg"
              onClick={(e) => {
                e.preventDefault()
                document.getElementById('hebergements')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
                history.pushState(null, '', '#hebergements')
              }}
            >
              Découvrir les hébergements
            </a>
          </div>
        </div>
        <div className="cta-media" aria-hidden="true">
          <FadingVideo src={heroVideoSrc} poster={heroPoster} className="cta-bg" />
        </div>
      </section>
    </div>
  )
}
