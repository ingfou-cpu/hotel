// HotelFormPage.jsx — Création/édition d'hôtel
import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiGet, apiPost, apiPatch, normalizeApiError } from '../../lib/api'
import { formatPrice } from '../../lib/format'
import Button from '../../components/Button'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Textarea from '../../components/Textarea'
import Checkbox from '../../components/Checkbox'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import Card from '../../components/Card'
import '../../pages/manager/manager.css'

const STAR_OPTIONS = [
  { value: 1, label: '1 étoile' },
  { value: 2, label: '2 étoiles' },
  { value: 3, label: '3 étoiles' },
  { value: 4, label: '4 étoiles' },
  { value: 5, label: '5 étoiles' }
]

export default function HotelFormPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id

  const [formData, setFormData] = useState({
    name: '',
    description: '',
    address: '',
    city: '',
    country: '',
    latitude: '',
    longitude: '',
    stars: 3,
    amenities: [],
    is_active: true
  })
  const [amenities, setAmenities] = useState([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})
  const [hotelImages, setHotelImages] = useState([])

  // Fetch amenities on mount
  useEffect(() => {
    let cancelled = false
    async function fetchAmenities() {
      try {
        const data = await apiGet('/amenities/')
        if (!cancelled) {
          setAmenities(data.results || data)
        }
      } catch {
        // Silent fail - amenities are optional
      }
    }
    fetchAmenities()
    return () => { cancelled = true }
  }, [])

  // Fetch hotel data if editing
  useEffect(() => {
    if (!isEdit) return
    let cancelled = false
    async function fetchHotel() {
      try {
        setLoading(true)
        const data = await apiGet(`/hotels/${id}/`)
        if (!cancelled) {
          setFormData({
            name: data.name || '',
            description: data.description || '',
            address: data.address || '',
            city: data.city || '',
            country: data.country || '',
            latitude: data.latitude !== null && data.latitude !== undefined ? String(data.latitude) : '',
            longitude: data.longitude !== null && data.longitude !== undefined ? String(data.longitude) : '',
            stars: data.stars || 3,
            amenities: (data.amenities || []).map(a => a.id),
            is_active: data.is_active !== false
          })
          setHotelImages(data.images || [])
        }
      } catch (err) {
        if (!cancelled) {
          const normalized = normalizeApiError(err)
          setError(normalized.message || 'Impossible de charger l\'hôtel')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    fetchHotel()
    return () => { cancelled = true }
  }, [id, isEdit])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
    // Clear field error on change
    if (fieldErrors[name]) {
      setFieldErrors(prev => {
        const next = { ...prev }
        delete next[name]
        return next
      })
    }
  }

  const handleAmenityChange = (amenityId, checked) => {
    setFormData(prev => ({
      ...prev,
      amenities: checked
        ? [...prev.amenities, amenityId]
        : prev.amenities.filter(a => a !== amenityId)
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setFieldErrors({})

    // Basic validation
    const errors = {}
    if (!formData.name.trim()) errors.name = 'Le nom est requis'
    if (!formData.address.trim()) errors.address = 'L\'adresse est requise'
    if (!formData.city.trim()) errors.city = 'La ville est requise'
    if (!formData.country.trim()) errors.country = 'Le pays est requis'
    if (formData.latitude && isNaN(Number(formData.latitude))) errors.latitude = 'Latitude invalide'
    if (formData.longitude && isNaN(Number(formData.longitude))) errors.longitude = 'Longitude invalide'

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }

    try {
      setSubmitting(true)
      const payload = {
        name: formData.name.trim(),
        description: formData.description.trim(),
        address: formData.address.trim(),
        city: formData.city.trim(),
        country: formData.country.trim(),
        latitude: formData.latitude ? Number(formData.latitude) : null,
        longitude: formData.longitude ? Number(formData.longitude) : null,
        stars: Number(formData.stars),
        amenities: formData.amenities,
        is_active: formData.is_active
      }

      if (isEdit) {
        await apiPatch(`/hotels/${id}/`, payload)
      } else {
        await apiPost('/hotels/', payload)
      }

      navigate('/back-office/hotels', { state: { success: isEdit ? 'Hôtel modifié avec succès' : 'Hôtel créé avec succès' } })
    } catch (err) {
      const normalized = normalizeApiError(err)
      setError(normalized.message)
      if (normalized.fieldErrors) {
        setFieldErrors(normalized.fieldErrors)
      }
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) {
    return (
      <div className="manager-page">
        <header className="manager-header">
          <h1>{isEdit ? 'Modifier l\'hôtel' : 'Nouvel hôtel'}</h1>
        </header>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Spinner size="lg" ariaLabel="Chargement" />
        </div>
      </div>
    )
  }

  return (
    <div className="manager-page">
      <header className="manager-header">
        <div>
          <h1>{isEdit ? 'Modifier l\'hôtel' : 'Nouvel hôtel'}</h1>
          <p>{isEdit ? 'Mettez à jour les informations de l\'hôtel' : 'Créez un nouvel hôtel pour votre portefeuille'}</p>
        </div>
        <Button as={Link} to="/back-office/hotels" variant="ghost">
          Annuler
        </Button>
      </header>

      {(error || (typeof window !== 'undefined' && window.location.search.includes('success'))) && (
        <Alert type={error ? 'error' : 'success'} dismissible onDismiss={() => { setError(null); if (typeof window !== 'undefined') window.history.replaceState({}, '', window.location.pathname) }} className="alert-fixed">
          {error || 'Opération réussie'}
        </Alert>
      )}

      <form className="manager-form" onSubmit={handleSubmit}>
        <section className="manager-form-section" aria-labelledby="info-title">
          <h2 id="info-title" className="manager-form-section-title">Informations générales</h2>
          <div className="manager-form-grid">
            <Input
              label="Nom *"
              name="name"
              value={formData.name}
              onChange={handleChange}
              error={fieldErrors.name}
              placeholder="Nom de l'hôtel"
              required
              autoComplete="organization"
            />
            <Select
              label="Étoiles *"
              name="stars"
              value={formData.stars}
              onChange={handleChange}
              error={fieldErrors.stars}
              options={STAR_OPTIONS}
              required
            />
          </div>
          <Textarea
            label="Description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            error={fieldErrors.description}
            placeholder="Description de l'hôtel, services, ambiance..."
            rows={4}
          />
        </section>

        <section className="manager-form-section" aria-labelledby="location-title">
          <h2 id="location-title" className="manager-form-section-title">Localisation</h2>
          <div className="manager-form-grid">
            <Input
              label="Adresse *"
              name="address"
              value={formData.address}
              onChange={handleChange}
              error={fieldErrors.address}
              placeholder="Numéro et rue"
              required
              autoComplete="street-address"
            />
            <Input
              label="Ville *"
              name="city"
              value={formData.city}
              onChange={handleChange}
              error={fieldErrors.city}
              placeholder="Ville"
              required
              autoComplete="address-level2"
            />
            <Input
              label="Pays *"
              name="country"
              value={formData.country}
              onChange={handleChange}
              error={fieldErrors.country}
              placeholder="Pays"
              required
              autoComplete="country"
            />
          </div>
          <div className="manager-form-grid">
            <Input
              label="Latitude"
              name="latitude"
              type="number"
              step="any"
              value={formData.latitude}
              onChange={handleChange}
              error={fieldErrors.latitude}
              placeholder="Ex : 48.8566"
              hint="Coordonnée GPS (optionnel)"
            />
            <Input
              label="Longitude"
              name="longitude"
              type="number"
              step="any"
              value={formData.longitude}
              onChange={handleChange}
              error={fieldErrors.longitude}
              placeholder="Ex : 2.3522"
              hint="Coordonnée GPS (optionnel)"
            />
          </div>
        </section>

        <section className="manager-form-section" aria-labelledby="amenities-title">
          <h2 id="amenities-title" className="manager-form-section-title">Équipements</h2>
          <p className="small muted" style={{ marginBottom: '12px' }}>Sélectionnez les équipements disponibles dans l'hôtel</p>
          <div className="amenities-grid" role="group" aria-label="Liste des équipements">
            {amenities.map(amenity => (
              <label key={amenity.id} className="amenity-item">
                <input
                  type="checkbox"
                  checked={formData.amenities.includes(amenity.id)}
                  onChange={(e) => handleAmenityChange(amenity.id, e.target.checked)}
                />
                <span>{amenity.icon ? <span className="amenity-icon" aria-hidden="true">{amenity.icon}</span> : null}{amenity.name}</span>
              </label>
            ))}
            {amenities.length === 0 && <p className="small muted">Aucun équipement disponible</p>}
          </div>
        </section>

        <section className="manager-form-section" aria-labelledby="status-title">
          <h2 id="status-title" className="manager-form-section-title">Statut</h2>
          <Checkbox
            label="Hôtel actif"
            name="is_active"
            checked={formData.is_active}
            onChange={handleChange}
            description="L'hôtel sera visible et réservable par les clients"
          />
        </section>

        {hotelImages.length > 0 && (
          <section className="manager-form-section" aria-labelledby="images-title">
            <h2 id="images-title" className="manager-form-section-title">Images actuelles (lecture seule)</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(120px, 1fr))', gap: '12px' }}>
              {hotelImages.map((img, idx) => (
                <div key={idx} style={{ position: 'relative', aspectRatio: '4/3', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--color-border)' }}>
                  <img src={typeof img === 'string' ? img : img.image || img.url} alt={`Image ${idx + 1}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} loading="lazy" />
                </div>
              ))}
            </div>
            <p className="small muted">Les images sont gérées séparément dans l'interface d'administration Django.</p>
          </section>
        )}

        <div className="manager-form-actions">
          <Button as={Link} to="/back-office/hotels" variant="secondary">Annuler</Button>
          <Button type="submit" variant="primary" loading={submitting}>
            {isEdit ? 'Enregistrer les modifications' : 'Créer l\'hôtel'}
          </Button>
        </div>
      </form>
    </div>
  )
}