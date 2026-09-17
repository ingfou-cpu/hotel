import React, { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { normalizeApiError } from '../lib/api'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Input from '../components/Input'

export default function RegisterPage(){
  const { register } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const from = location.state?.from || '/'

  const [form, setForm] = useState({ email:'', password:'', first_name:'', last_name:'', phone:'' })
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState(null)
  const [submitting, setSubmitting] = useState(false)

  const handleChange = (k,v)=> setForm(prev=> ({...prev, [k]:v}))

  const handleSubmit = async(e)=>{
    e.preventDefault()
    setError(''); setFieldErrors(null)
    if(form.password.length < 8){ setError('Le mot de passe doit contenir au moins 8 caractères.'); return }
    setSubmitting(true)
    try{
      await register({ email: form.email, password: form.password, first_name: form.first_name, last_name: form.last_name, phone: form.phone || undefined })
      navigate(from, { replace:true })
    }catch(err){
      const { message, fieldErrors: fe } = normalizeApiError(err)
      if(fe) setFieldErrors(fe)
      setError(message || 'Inscription impossible.')
    } finally{ setSubmitting(false)}
  }

  return (
    <div className="container page">
      <div className="auth-wrap">
        <div className="auth-visual">
          <div>
            <p className="eyebrow" style={{ color:'var(--color-accent)' }}>Nouveau chez nous</p>
            <h1 style={{ fontFamily:'var(--font-display)', fontSize:'2rem', lineHeight:1, marginTop:8, fontWeight:400 }}>Créez<br/>votre compte.</h1>
            <p style={{ marginTop:12, color:'var(--color-text-secondary)', lineHeight:1.6 }}>Gérez vos réservations, enregistrez vos hôtels favoris et recevez vos confirmations par e-mail.</p>
          </div>
          <div className="liquid-glass" style={{ borderRadius:14, padding:14, display:'flex', flexDirection:'column', gap:6 }}>
            <div style={{ fontWeight:700, color:'var(--color-text)' }}>Avantage</div>
            <div className="small muted">Confirmation instantanée et reçus accessibles depuis « Mes réservations ».</div>
          </div>
        </div>

        <div className="auth-form">
          <h2 style={{ fontFamily:'var(--font-display)', fontSize:'1.45rem', marginBottom:6 }}>Inscription</h2>
          <p className="small muted" style={{ marginBottom:16 }}>Tous les champs marqués d'une étoile sont requis.</p>
          {error && <div style={{ marginBottom:14 }}><Alert type="error">{error}</Alert></div>}

          <form onSubmit={handleSubmit} style={{ display:'flex', flexDirection:'column', gap:12 }}>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <Input label="Prénom" name="first_name" value={form.first_name} onChange={e=>handleChange('first_name', e.target.value)} required error={fieldErrors?.first_name} />
              <Input label="Nom" name="last_name" value={form.last_name} onChange={e=>handleChange('last_name', e.target.value)} required error={fieldErrors?.last_name} />
            </div>
            <Input label="Adresse e-mail" type="email" name="email" value={form.email} onChange={e=>handleChange('email', e.target.value)} placeholder="vous@exemple.fr" required autoComplete="email" error={fieldErrors?.email} />
            <Input label="Téléphone (optionnel)" type="tel" name="phone" value={form.phone} onChange={e=>handleChange('phone', e.target.value)} placeholder="+33 6 00 00 00 00" autoComplete="tel" error={fieldErrors?.phone} />
            <Input label="Mot de passe" type="password" name="password" value={form.password} onChange={e=>handleChange('password', e.target.value)} placeholder="Au moins 8 caractères" required autoComplete="new-password" hint="Minimum 8 caractères" error={fieldErrors?.password} />
            {fieldErrors?.non_field_errors && <Alert type="error">{fieldErrors.non_field_errors}</Alert>}
            <Button type="submit" size="lg" loading={submitting} className="btn-block">Créer mon compte</Button>
          </form>

          <p className="small" style={{ marginTop:16, textAlign:'center' }}>
            Déjà inscrit ? <Link to="/connexion" state={{ from }} style={{ fontWeight:700, textDecoration:'underline', textUnderlineOffset:3 }}>Se connecter</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
