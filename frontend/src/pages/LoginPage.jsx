import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { normalizeApiError } from '../lib/api'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Input from '../components/Input'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/'

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e)=>{
    e.preventDefault()
    setError(''); setFieldErrors(null)
    if(!email || !password){ setError('Veuillez renseigner votre e-mail et votre mot de passe.'); return }
    setSubmitting(true)
    try{
      await login(email, password)
      navigate(from, { replace:true })
    }catch(err){
      const { message, fieldErrors: fe } = normalizeApiError(err)
      if(fe) setFieldErrors(fe)
      // DRF often returns non_field_errors or detail
      const isBadCreds = err.response?.status === 401 || /incorrect|invalid|identifiants/i.test(message)
      setError(isBadCreds ? 'Identifiants incorrects. Vérifiez votre e-mail et votre mot de passe.' : (message || 'Connexion impossible.'))
    } finally{ setSubmitting(false)}
  }

  return (
    <div className="container page">
      <div className="auth-wrap">
        <div className="auth-visual">
          <div>
            <p className="eyebrow" style={{ color:'var(--color-accent)' }}>Bienvenue</p>
            <h1 style={{ fontFamily:'var(--font-display)', fontSize:'2rem', lineHeight:1, marginTop:8, fontWeight:400 }}>Ravi de vous<br/>revoir.</h1>
            <p style={{ marginTop:12, color:'var(--color-text-secondary)', lineHeight:1.6 }}>Accédez à vos réservations, vos favoris et vos notifications. Paiement sécurisé pour vos prochains séjours.</p>
          </div>
          <div className="liquid-glass" style={{ borderRadius:14, padding:14 }}>
            <div style={{ fontWeight:700, fontSize:'0.9rem', color:'var(--color-text)' }}>Hôtel Lumière</div>
            <div className="small muted">Séjours d'exception, service attentif.</div>
          </div>
        </div>

        <div className="auth-form">
          <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.45rem', marginBottom:6 }}>Connexion</h2>
          <p className="small muted" style={{ marginBottom:16 }}>Saisissez vos identifiants pour continuer.</p>

          {error && <div style={{ marginBottom:14 }}><Alert type="error">{error}</Alert></div>}

          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:14 }}>
            <Input label="Adresse e-mail" type="email" name="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="vous@exemple.fr" required autoComplete="email" error={fieldErrors?.email} />
            <Input label="Mot de passe" type="password" name="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" required autoComplete="current-password" error={fieldErrors?.password} />
            <Button type="submit" size="lg" loading={submitting} className="btn-block">Se connecter</Button>
          </form>

          <p className="small" style={{ marginTop:16, textAlign:'center' }}>
            Pas encore de compte ? <Link to="/inscription" state={{ from }} style={{ fontWeight:700, textDecoration:'underline', textUnderlineOffset:3 }}>Créer un compte</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
