import React, { useMemo, useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
// Motion for React — subpath "motion/react" exposes the same API as framer-motion via the `motion` package
import { motion } from 'motion/react'
import '../styles/news.css'

function useReducedMotion() {
  const [reduced, setReduced] = useState(false)
  useEffect(() => {
    const m = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(m.matches)
    const onChange = (e) => setReduced(e.matches)
    m.addEventListener ? m.addEventListener('change', onChange) : m.addListener(onChange)
    return () => { m.removeEventListener ? m.removeEventListener('change', onChange) : m.removeListener(onChange) }
  }, [])
  return reduced
}

// ——— Hardcoded editorial data (FR) ———
const ARTICLES = [
  {
    id: 1,
    featured: true,
    index: '01',
    cat: 'Maisons',
    catTone: 'champagne',
    date: '12 septembre 2026',
    reading: '4 min',
    title: 'Une nouvelle aile s’ouvre au Pavillon Lumière — lumière naturelle et silence',
    lede: 'Sept suites sous verrière, un jardin d’hiver et une bibliothèque suspendue : l’extension la plus attendue de la saison prend le parti du calme et de la matière.',
    author: 'Claire Morel',
    role: 'Rédactrice en chef',
    avatar: 'https://i.pravatar.cc/100?img=32',
    image: 'https://images.unsplash.com/photo-1520250497591-112f2f40a3f4?auto=format&fit=crop&w=1400&q=80',
  },
  {
    id: 2,
    index: '02',
    cat: 'Design',
    catTone: 'cyan',
    date: '28 août 2026',
    reading: '3 min',
    title: 'Le textile comme architecture : quand le lin structure la chambre',
    lede: 'Des rideaux à la tête de lit, une même étoffe, une même exigence acoustique. Visite d’un atelier où le geste compte plus que l’effet.',
    author: 'Noah Becker',
    image: 'https://images.unsplash.com/photo-1611892440504-42a792e24d32?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 3,
    index: '03',
    cat: 'Culinaire',
    catTone: 'champagne',
    date: '21 août 2026',
    reading: '5 min',
    title: 'Cuisine de cueillette : le potager du soir au Domaine des Cimes',
    lede: 'À 1 400 mètres, le chef compose au rythme des herbes alpines — une carte courte, une justesse rare.',
    author: 'Inès Fabre',
    image: 'https://images.unsplash.com/photo-1414235077428-338989a2e8c0?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 4,
    index: '04',
    cat: 'Culture',
    catTone: 'cyan',
    date: '14 août 2026',
    reading: '3 min',
    title: 'Nuits photographiques : le hall se fait galerie',
    lede: 'Tirages grand format, lumière rasante, silence — une programmation pensée comme une respiration nocturne.',
    author: 'Yanis El Amrani',
    image: 'https://images.unsplash.com/photo-1518998053901-5348d3961a04?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 5,
    index: '05',
    cat: 'Durable',
    catTone: 'champagne',
    date: '05 août 2026',
    reading: '4 min',
    title: 'Mesurer l’empreinte sans renoncer au plaisir du séjour',
    lede: 'De la buanderie à la chaudière, les coulisses d’un hôtel qui réduit sans afficher — récit d’une transformation sobre.',
    author: 'Sofia Klein',
    image: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 6,
    index: '06',
    cat: 'Design',
    catTone: 'cyan',
    date: '29 juillet 2026',
    reading: '3 min',
    title: 'L’art du seuil : portes, passages et transitions',
    lede: 'Ce moment où l’on quitte la rue pour entrer ailleurs — enquête sur les seuils qui font l’hospitalité.',
    author: 'Hugo Martin',
    image: 'https://images.unsplash.com/photo-1560448204-603b3fc33ddc?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 7,
    index: '07',
    cat: 'Maisons',
    catTone: 'champagne',
    date: '18 juillet 2026',
    reading: '2 min',
    title: 'Villa Nuit Blanche : dormir face à la Méditerranée',
    lede: 'Une maison blanche, trois terrasses, une seule direction : l’horizon. Carnet d’un week-end suspendu.',
    author: 'Léa Durand',
    image: 'https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?auto=format&fit=crop&w=900&q=80',
  },
  {
    id: 8,
    index: '08',
    cat: 'Culture',
    catTone: 'cyan',
    date: '09 juillet 2026',
    reading: '6 min',
    title: 'Cartographie sensible : les villes où l’on marche le mieux',
    lede: 'De Lyon à Lisbonne, cinq itinéraires à pied qui changent le regard — et les adresses où s’arrêter.',
    author: 'Milo Rousseau',
    image: 'https://images.unsplash.com/photo-1477959858617-67f85cf4f1df?auto=format&fit=crop&w=900&q=80',
  },
]

const CATEGORIES = ['Tout', 'Maisons', 'Design', 'Culinaire', 'Culture', 'Durable']

const TICKER = [
  'Ouverture — Pavillon Lumière, aile Jardin d’hiver',
  'Saison d’hiver 2026 — pré-réservations ouvertes',
  'Atelier chefs — cueillette alpine au Domaine des Cimes',
  'Nuits photographiques — hall transformé en galerie',
  'Hôtel Lumière — Actualités en direct',
]

function NewsPage() {
  const shouldReduce = useReducedMotion()
  const [active, setActive] = useState('Tout')
  const [query, setQuery] = useState('')
  const [newsletter, setNewsletter] = useState('')
  const [nlError, setNlError] = useState('')
  const [nlSuccess, setNlSuccess] = useState('')

  const featured = ARTICLES.find((a) => a.featured)
  const rail = ARTICLES.slice(1, 4) // 02-04 for rail
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return ARTICLES.filter((a) => {
      const catOk = active === 'Tout' || a.cat === active
      const qOk = !q || a.title.toLowerCase().includes(q) || a.lede.toLowerCase().includes(q) || a.cat.toLowerCase().includes(q)
      return catOk && qOk
    }).filter((a) => !a.featured) // featured shown separately
  }, [active, query])

  const handleNewsletter = (e) => {
    e.preventDefault()
    const v = newsletter.trim()
    const ok = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
    if (!ok) {
      setNlError('Veuillez saisir une adresse e-mail valide.')
      setNlSuccess('')
      return
    }
    setNlError('')
    setNlSuccess('Merci — vous êtes inscrit·e. À très vite dans votre boîte.')
    setNewsletter('')
  }

  // Motion variants
  const container = {
    hidden: {},
    visible: { transition: { staggerChildren: shouldReduce ? 0 : 0.08, delayChildren: shouldReduce ? 0 : 0.06 } },
  }
  const item = {
    hidden: { opacity: 0, y: shouldReduce ? 0 : 18, filter: shouldReduce ? 'none' : 'blur(6px)' },
    visible: { opacity: 1, y: 0, filter: 'blur(0px)', transition: { duration: 0.62, ease: [0.2, 0.8, 0.2, 1] } },
  }

  return (
    <div className="news-page">
      {/* HUD */}
      <div className="news-hud">
        <div className="container news-hud-inner">
          <div className="news-hud-left">
            <span className="news-hud-live"><span className="news-hud-dot" aria-hidden="true" /> En direct</span>
            <span className="news-hud-sep" aria-hidden="true" />
            <span>Édition — 15 septembre 2026</span>
            <span className="news-hud-sep" aria-hidden="true" />
            <span className="news-hud-id">HL / ACTU — 08 articles</span>
          </div>
          <div className="news-hud-right">
            <span>Paris · 21:04 — UTC+2</span>
            <span className="news-hud-sep" aria-hidden="true" />
            <span style={{ color: 'var(--color-accent)', fontWeight: 800 }}>Hôtel Lumière — Newsroom</span>
          </div>
        </div>
      </div>

      {/* Hero */}
      <section className="news-hero" aria-labelledby="news-title">
        <div className="news-hero-bg" aria-hidden="true">
          <div className="news-grid" />
          <div className="news-scanlines" />
          <div className="news-hero-aurora">
            <span className="news-aurora news-aurora--1" />
            <span className="news-aurora news-aurora--2" />
          </div>
        </div>

        <div className="container news-hero-inner">
          <motion.div
            initial={shouldReduce ? false : { opacity: 0, y: 16, filter: 'blur(8px)' }}
            animate={shouldReduce ? {} : { opacity: 1, y: 0, filter: 'blur(0px)' }}
            transition={{ duration: 0.7, ease: [0.2, 0.8, 0.2, 1] }}
          >
            <p className="news-kicker"><i aria-hidden="true" /> Journal — Saison 2026 <span style={{ color: 'var(--news-cyan)', fontWeight: 800 }}>· Système en veille lumineuse</span></p>
            <h1 id="news-title" className="news-title">
              Actualités <em>—</em> <span className="thin">le calme</span><br />
              <span style={{ color: 'rgba(255,255,255,0.92)' }}>du temps</span> <em>long</em> <span className="cyan" aria-hidden="true">HL_009</span>
            </h1>
            <p className="news-subtitle">
              Une rédaction <strong>courte et choisie</strong> — ouvertures, gestes d’atelier, tables et itinéraires. Une page pensée comme une salle de lecture : verre sombre, <span style={{ color: 'var(--news-cyan)' }}>grille de précision</span>, et ce souffle champagne qui fait la lumière.
            </p>

            <div className="news-hero-meta">
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {CATEGORIES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    className={`news-chip ${active === c ? 'active' : ''}`}
                    onClick={() => setActive(c)}
                    aria-pressed={active === c}
                  >
                    {c}
                  </button>
                ))}
              </div>

              <label className="news-search" aria-label="Rechercher dans les actualités">
                <span className="visually-hidden">Rechercher</span>
                <input
                  type="search"
                  placeholder="Rechercher — titre, thème…"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                />
                <button type="button" aria-label="Rechercher" onClick={() => {}}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <circle cx="11" cy="11" r="7" stroke="currentColor" strokeWidth="1.8" />
                    <path d="M16 16l4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
                  </svg>
                </button>
              </label>
            </div>

            <div style={{ marginTop: 14, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
              <span className="small" style={{ color: 'rgba(255,255,255,0.58)', fontWeight: 600, fontVariantNumeric: 'tabular-nums' }}>
                08 articles · Lecture moyenne 3–4 min · Mise à jour quotidienne
              </span>
              <span style={{ width: 1, height: 14, background: 'var(--news-hairline)' }} aria-hidden="true" />
              <span className="small" style={{ color: 'var(--color-accent)', fontWeight: 800, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: '0.72rem' }}>
                Filtres synchronisés — URL préservée
              </span>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Ticker */}
      <div className="news-ticker" role="region" aria-label="Fil d’actualités">
        <div className="container" style={{ overflow: 'hidden' }}>
          {shouldReduce ? (
            <div className="news-ticker-track" style={{ flexWrap: 'wrap', gap: 12 }}>
              {TICKER.map((t) => (
                <span key={t} className="news-ticker-item">
                  <span className="news-ticker-dot" aria-hidden="true" />
                  {t}
                </span>
              ))}
            </div>
          ) : (
            <motion.div
              className="news-ticker-track"
              animate={{ x: ['0%', '-50%'] }}
              transition={{ duration: 28, ease: 'linear', repeat: Infinity }}
              style={{ width: 'max-content' }}
              aria-hidden="true"
            >
              {[...TICKER, ...TICKER].map((t, i) => (
                <span key={`${t}-${i}`} className="news-ticker-item">
                  <span className="news-ticker-dot" />
                  <strong>{t.split(' — ')[0]}</strong>
                  {t.includes(' — ') && <span>— {t.split(' — ').slice(1).join(' — ')}</span>}
                </span>
              ))}
              {[...TICKER, ...TICKER].map((t, i) => (
                <span key={`${t}-dup-${i}`} className="news-ticker-item">
                  <span className="news-ticker-dot" />
                  <strong>{t.split(' — ')[0]}</strong>
                  {t.includes(' — ') && <span>— {t.split(' — ').slice(1).join(' — ')}</span>}
                </span>
              ))}
            </motion.div>
          )}
        </div>
      </div>

      {/* Featured + rail */}
      <section className="container news-featured-wrap" aria-labelledby="featured-heading">
        <div className="news-featured-grid">
          <motion.article
            className="news-featured"
            initial={shouldReduce ? false : { opacity: 0, y: 18 }}
            whileInView={shouldReduce ? {} : { opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.62, ease: [0.2, 0.8, 0.2, 1] }}
            whileHover={shouldReduce ? {} : { y: -3 }}
          >
            <div className="news-featured-media">
              <img src={featured.image} alt="" loading="eager" />
              <span className="news-featured-badge"><i aria-hidden="true" /> À la une</span>
              <div className="news-featured-corners" aria-hidden="true" />
              <div className="news-shimmer" aria-hidden="true" />
            </div>
            <div className="news-featured-body">
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span className="news-index"><span>01</span> — {featured.cat}</span>
                <span className={`news-cat ${featured.catTone === 'cyan' ? 'news-cat--cyan' : ''}`}>{featured.cat}</span>
                <span style={{ marginLeft: 'auto', fontSize: '0.70rem', fontWeight: 700, color: 'var(--color-text-muted)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>{featured.date} · {featured.reading}</span>
              </div>
              <h2 id="featured-heading" className="news-featured-title">
                {featured.title.split(' — ')[0]} — <em>{featured.title.split(' — ')[1]}</em>
              </h2>
              <p className="news-featured-lede">{featured.lede}</p>
              <div className="news-featured-foot">
                <span className="news-author">
                  <img src={featured.avatar} alt="" width={28} height={28} />
                  {featured.author} · <span style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>{featured.role}</span>
                </span>
                <Link to="/" className="news-read" aria-label="Lire l’article à la une">
                  Lire l’article
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M8 5l8 7-8 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </Link>
              </div>
            </div>
          </motion.article>

          <aside className="news-rail" aria-label="Tendances">
            <div className="news-rail-head">
              <h3><i aria-hidden="true" /> Tendances</h3>
              <small>Index 02→04</small>
            </div>
            <div className="news-rail-list">
              {rail.map((a) => (
                <Link key={a.id} to="/" className="news-rail-item">
                  <span className="news-rail-num" aria-hidden="true">{a.index}</span>
                  <div>
                    <h4>{a.title}</h4>
                    <p>{a.lede}</p>
                    <div className="news-rail-meta">
                      <span style={{ color: a.catTone === 'cyan' ? 'var(--news-cyan)' : 'var(--color-accent)' }}>{a.cat}</span>
                      <span className="dot" aria-hidden="true" />
                      <span>{a.date}</span>
                      <span className="dot" aria-hidden="true" />
                      <span>{a.reading}</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
            <div style={{ padding: '12px 18px', borderTop: '1px solid var(--news-hairline)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(255,255,255,0.02)' }}>
              <span className="small" style={{ color: 'var(--color-text-muted)', fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', fontSize: '0.70rem' }}>Flux continu — 08 articles</span>
              <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-accent)', boxShadow: '0 0 10px rgba(231,185,129,0.5)' }} aria-hidden="true" />
            </div>
          </aside>
        </div>
      </section>

      {/* Filterbar sticky */}
      <div className="container">
        <div className="news-filterbar" role="toolbar" aria-label="Filtrer les actualités">
          <span className="news-filterbar-label">Filtrer</span>
          {CATEGORIES.map((c) => (
            <button key={c} type="button" className={`news-chip ${active === c ? 'active' : ''}`} onClick={() => setActive(c)} aria-pressed={active === c}>
              {c}
            </button>
          ))}
          <span className="news-count">{filtered.length} article{filtered.length !== 1 ? 's' : ''} · {active === 'Tout' ? 'toutes catégories' : active.toLowerCase()}</span>
        </div>
      </div>

      {/* Feed grid */}
      <section className="container news-feed" aria-label="Tous les articles">
        {filtered.length === 0 ? (
          <div className="news-empty">
            <h4>Aucun article pour « {active} »{query ? ` — « ${query} »` : ''}</h4>
            <p className="small muted" style={{ marginTop: 6 }}>Essayez « Tout » ou élargissez votre recherche.</p>
            <button type="button" className="btn btn-secondary btn-sm" style={{ marginTop: 14 }} onClick={() => { setActive('Tout'); setQuery('') }}>
              Réinitialiser les filtres
            </button>
          </div>
        ) : (
          <motion.div
            className="news-grid-cards"
            variants={container}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.12 }}
          >
            {filtered.map((a) => (
              <motion.article key={a.id} variants={item} className="news-card" whileHover={shouldReduce ? {} : { y: -4 }}>
                <div className="news-card-media">
                  <img src={a.image} alt="" loading="lazy" />
                  <div className="news-card-top">
                    <span className="news-card-index">{a.index}</span>
                    <span className={`news-card-cat ${a.catTone === 'cyan' ? 'cyan' : ''}`}>{a.cat}</span>
                  </div>
                </div>
                <div className="news-card-body">
                  <h3 className="news-card-title">
                    {a.title.includes(' : ') ? (
                      <>
                        {a.title.split(' : ')[0]} : <em>{a.title.split(' : ').slice(1).join(' : ')}</em>
                      </>
                    ) : a.title.includes(' — ') ? (
                      <>
                        {a.title.split(' — ')[0]} — <em>{a.title.split(' — ').slice(1).join(' — ')}</em>
                      </>
                    ) : (
                      a.title
                    )}
                  </h3>
                  <p className="news-card-lede">{a.lede}</p>
                  <div className="news-card-foot">
                    <time dateTime={a.date}>{a.date}</time>
                    <span className="reading"><i aria-hidden="true" /> {a.reading} · {a.author}</span>
                  </div>
                  <span className="news-card-cta" aria-hidden="true">
                    Lire <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M7 12h10M13 6l6 6-6 6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </span>
                </div>
                <div className="news-card-hud" aria-hidden="true" />
                <Link to="/" aria-label={`Lire — ${a.title}`} style={{ position: 'absolute', inset: 0, borderRadius: 'inherit' }} />
              </motion.article>
            ))}
          </motion.div>
        )}
      </section>

      {/* Newsletter CTA */}
      <section className="container" aria-labelledby="cta-news-title">
        <motion.div
          className="news-cta"
          initial={shouldReduce ? false : { opacity: 0, y: 18 }}
          whileInView={shouldReduce ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
        >
          <div className="news-cta-visual" aria-hidden="true">
            <img src="https://images.unsplash.com/photo-1551882547-b79c4176354d?auto=format&fit=crop&w=1200&q=80" alt="" loading="lazy" />
            <div className="news-cta-visual-grid" />
          </div>
          <div className="news-cta-body">
            <p className="news-kicker" style={{ color: 'var(--news-cyan)' }}><i style={{ background: 'var(--news-cyan)' }} aria-hidden="true" /> Lettre — chaque vendredi</p>
            <h3 id="cta-news-title">Restez dans la <em>lumière</em> — sans bruit</h3>
            <p>
              Une sélection courte : ouvertures, tables d’hôtes et itinéraires à pied. Pas de promotions agressives — seulement le nécessaire, envoyé avec soin.
            </p>
            <form className="news-cta-form" noValidate onSubmit={handleNewsletter}>
              <label htmlFor="news-email" className="visually-hidden">Adresse e-mail</label>
              <input
                id="news-email"
                type="email"
                placeholder="Votre e-mail"
                value={newsletter}
                onChange={(e) => { setNewsletter(e.target.value); if (nlError) setNlError('') }}
                aria-invalid={!!nlError}
                aria-describedby={nlError ? 'news-email-error' : nlSuccess ? 'news-email-success' : undefined}
                className={nlError ? 'error' : ''}
                autoComplete="email"
              />
              <button type="submit" className="btn btn-primary">S’abonner</button>
            </form>
            {nlError && <p id="news-email-error" className="news-cta-msg error" role="alert">{nlError}</p>}
            {nlSuccess && <p id="news-email-success" className="news-cta-msg success" role="status">{nlSuccess}</p>}
            <div className="news-cta-meta">
              <span>Envoi hebdomadaire</span><i aria-hidden="true" /><span>Désabonnement en un clic</span><i aria-hidden="true" /><span style={{ color: 'var(--color-accent)' }}>Aucun spam</span>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Closing index bar */}
      <div className="container" style={{ paddingBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '14px 16px', borderRadius: 'var(--radius-md)', border: '1px solid var(--news-hairline)', background: 'rgba(255,255,255,0.02)', backdropFilter: 'blur(10px)', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '0.70rem', fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>Index de la rédaction</span>
          <span style={{ width: 1, height: 14, background: 'var(--news-hairline)' }} aria-hidden="true" />
          <span className="small" style={{ color: 'var(--color-text-secondary)', fontWeight: 600 }}>
            01 Pavillon Lumière · 02 Textile · 03 Cueillette · 04 Photographie · 05 Empreinte · 06 Seuil · 07 Villa · 08 Cartographie
          </span>
          <Link to="/" className="news-read" style={{ marginLeft: 'auto' }}>
            Retour à l’accueil <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M8 5l8 7-8 7" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </Link>
        </div>
      </div>
    </div>
  )
}

export default NewsPage
