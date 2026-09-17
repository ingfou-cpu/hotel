import React, { useState } from 'react'
import { useAuth } from '../lib/auth'
import { normalizeApiError } from '../lib/api'
import Alert from '../components/Alert'
import Button from '../components/Button'
import Input from '../components/Input'
import Badge from '../components/Badge'
import Modal from '../components/Modal'
import { useNavigate } from 'react-router-dom'

export default function ProfilePage(){
  const { user, updateProfile, changePassword, deleteAccount } = useAuth()
  const navigate = useNavigate()

  const [profileForm, setProfileForm] = useState({ first_name: user?.first_name || '', last_name: user?.last_name || '', phone: user?.phone || '' })
  const [profileMsg, setProfileMsg] = useState('')
  const [profileErr, setProfileErr] = useState('')
  const [profileFieldErrors, setProfileFieldErrors] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  const [pwdForm, setPwdForm] = useState({ current_password:'', new_password:'', new_password_confirm:'' })
  const [pwdMsg, setPwdMsg] = useState('')
  const [pwdErr, setPwdErr] = useState('')
  const [pwdFieldErrors, setPwdFieldErrors] = useState(null)
  const [pwdLoading, setPwdLoading] = useState(false)

  const [deleteOpen, setDeleteOpen] = useState(false)
  const [deleteErr, setDeleteErr] = useState('')
  const [deleteLoading, setDeleteLoading] = useState(false)

  // sync when user changes
  React.useEffect(()=>{
    if(user) setProfileForm({ first_name: user.first_name||'', last_name: user.last_name||'', phone: user.phone||'' })
  },[user])

  const handleProfile = async(e)=>{
    e.preventDefault()
    setProfileErr(''); setProfileMsg(''); setProfileFieldErrors(null)
    setProfileLoading(true)
    try{
      await updateProfile({ first_name: profileForm.first_name, last_name: profileForm.last_name, phone: profileForm.phone || null })
      setProfileMsg('Profil mis à jour.')
    }catch(err){
      const {message, fieldErrors}=normalizeApiError(err)
      if(fieldErrors) setProfileFieldErrors(fieldErrors)
      setProfileErr(message)
    } finally{ setProfileLoading(false)}
  }

  const handlePassword = async(e)=>{
    e.preventDefault()
    setPwdErr(''); setPwdMsg(''); setPwdFieldErrors(null)
    if(pwdForm.new_password.length < 8){ setPwdErr('Le nouveau mot de passe doit contenir au moins 8 caractères.'); return }
    if(pwdForm.new_password !== pwdForm.new_password_confirm){ setPwdErr('La confirmation ne correspond pas.'); return }
    setPwdLoading(true)
    try{
      await changePassword(pwdForm)
      setPwdMsg('Mot de passe modifié. Veuillez vous reconnecter.')
      setTimeout(()=> navigate('/connexion'), 1200)
    }catch(err){
      const {message, fieldErrors}=normalizeApiError(err)
      if(fieldErrors) setPwdFieldErrors(fieldErrors)
      setPwdErr(message)
    } finally{ setPwdLoading(false)}
  }

  const handleDelete = async()=>{
    setDeleteErr(''); setDeleteLoading(true)
    try{
      await deleteAccount()
      navigate('/')
    }catch(err){
      const {message}=normalizeApiError(err); setDeleteErr(message)
    } finally{ setDeleteLoading(false)}
  }

  if(!user) return null

  const avatarUrl = user.avatar || null
  const roleLabel = user.role === 'hotel_manager' ? 'Gestionnaire' : user.role === 'admin' ? 'Administrateur' : 'Client'

  return (
    <div className="container page" style={{ maxWidth:860 }}>
      <div className="page-header">
        <p className="eyebrow">Compte</p>
        <h1>Profil</h1>
        <p>Gérez vos informations personnelles, votre mot de passe et votre compte.</p>
      </div>

      <div className="card" style={{ marginBottom:20 }}>
        <div className="card-body" style={{ display:'flex', gap:16, alignItems:'center', flexWrap:'wrap' }}>
          <div style={{ width:72, height:72, borderRadius:'50%', overflow:'hidden', background:'rgba(255,255,255,0.05)', flexShrink:0, display:'grid', placeItems:'center', border:'1px solid var(--color-border)' }}>
            {avatarUrl ? <img src={avatarUrl} alt="" style={{ width:'100%', height:'100%', objectFit:'cover' }} onError={e=>{e.currentTarget.style.display='none'}} /> : <span style={{ fontWeight:700, fontSize:'1.4rem', color:'var(--color-text-secondary)' }}>{(user.first_name?.[0] || user.email[0] || '?').toUpperCase()}</span>}
          </div>
          <div style={{ flex:1 }}>
            <div style={{ fontFamily:'var(--font-display)', fontSize:'1.2rem', fontWeight:700 }}>{user.first_name} {user.last_name}</div>
            <div className="small muted">{user.email}</div>
            <div style={{ marginTop:6 }}><Badge color={user.role==='hotel_manager' || user.role==='admin' ? 'info' : 'neutral'}>{roleLabel}</Badge></div>
          </div>
        </div>
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:20, alignItems:'start' }}>
        <form onSubmit={handleProfile} className="card">
          <div className="card-header"><h3 style={{ margin:0 }}>Informations personnelles</h3></div>
          <div className="card-body" style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {profileMsg && <Alert type="success">{profileMsg}</Alert>}
            {profileErr && <Alert type="error">{profileErr}</Alert>}
            <Input label="Prénom" name="first_name" value={profileForm.first_name} onChange={e=>setProfileForm({...profileForm, first_name:e.target.value})} error={profileFieldErrors?.first_name} required />
            <Input label="Nom" name="last_name" value={profileForm.last_name} onChange={e=>setProfileForm({...profileForm, last_name:e.target.value})} error={profileFieldErrors?.last_name} required />
            <Input label="Téléphone" name="phone" type="tel" value={profileForm.phone} onChange={e=>setProfileForm({...profileForm, phone:e.target.value})} error={profileFieldErrors?.phone} placeholder="+33 6 00 00 00 00" />
            <Button type="submit" loading={profileLoading}>Enregistrer</Button>
          </div>
        </form>

        <form onSubmit={handlePassword} className="card">
          <div className="card-header"><h3 style={{ margin:0 }}>Changer le mot de passe</h3></div>
          <div className="card-body" style={{ display:'flex', flexDirection:'column', gap:12 }}>
            {pwdMsg && <Alert type="success">{pwdMsg}</Alert>}
            {pwdErr && <Alert type="error">{pwdErr}</Alert>}
            <Input label="Mot de passe actuel" type="password" name="current_password" value={pwdForm.current_password} onChange={e=>setPwdForm({...pwdForm, current_password:e.target.value})} error={pwdFieldErrors?.current_password} required autoComplete="current-password" />
            <Input label="Nouveau mot de passe" type="password" name="new_password" value={pwdForm.new_password} onChange={e=>setPwdForm({...pwdForm, new_password:e.target.value})} error={pwdFieldErrors?.new_password} required autoComplete="new-password" hint="Minimum 8 caractères" />
            <Input label="Confirmer le nouveau mot de passe" type="password" name="new_password_confirm" value={pwdForm.new_password_confirm} onChange={e=>setPwdForm({...pwdForm, new_password_confirm:e.target.value})} error={pwdFieldErrors?.new_password_confirm} required autoComplete="new-password" />
            <Button type="submit" variant="secondary" loading={pwdLoading}>Modifier le mot de passe</Button>
            <p className="small muted" style={{ fontSize:'0.78rem' }}>Après modification, vous serez déconnecté et invité à vous reconnecter.</p>
          </div>
        </form>
      </div>

      <div className="card" style={{ marginTop:20, borderColor:'#F5C2C4' }}>
        <div className="card-body">
          <h3 style={{ fontFamily:'var(--font-display)', fontSize:'1.05rem', color:'var(--color-danger)' }}>Supprimer le compte</h3>
          <p className="small muted" style={{ marginTop:6, lineHeight:1.6 }}>La suppression est définitive. Si vous avez des réservations à venir, la suppression sera refusée.</p>
          <div style={{ marginTop:12 }}>
            <Button variant="danger" onClick={()=>setDeleteOpen(true)}>Supprimer mon compte</Button>
          </div>
        </div>
      </div>

      <Modal open={deleteOpen} onClose={()=>setDeleteOpen(false)} title="Confirmer la suppression" footer={
        <>
          <Button variant="secondary" onClick={()=>setDeleteOpen(false)}>Annuler</Button>
          <Button variant="danger" onClick={handleDelete} loading={deleteLoading}>Confirmer la suppression</Button>
        </>
      }>
        {deleteErr && <div style={{ marginBottom:12 }}><Alert type="error">{deleteErr}</Alert></div>}
        <p className="small" style={{ lineHeight:1.6 }}>Cette action supprimera votre compte et vos données personnelles. Les réservations associées seront conservées côté établissement si la réglementation l'exige, mais vous ne pourrez plus y accéder.</p>
        <p className="small muted" style={{ marginTop:8 }}>Tapez sur « Confirmer » pour poursuivre.</p>
      </Modal>

      <style>{`@media(max-width: 760px){ div[style*="gridTemplateColumns:1fr 1fr"]{ grid-template-columns:1fr !important; } }`}</style>
    </div>
  )
}
