// RoomFormPage.jsx — Création/édition de chambre
import React, { useEffect, useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { apiGet, apiPost, apiPatch, normalizeApiError } from '../../lib/api'
import { ROOM_TYPES } from '../../lib/constants'
import { formatPrice } from '../../lib/format'
import Button from '../../components/Button'
import Input from '../../components/Input'
import Select from '../../components/Select'
import Textarea from '../../components/Textarea'
import Checkbox from '../../components/Checkbox'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import '../../pages/manager/manager.css'

const ROOM_TYPE_OPTIONS = Object.entries(ROOM_TYPES).map(([value, label]) => ({ value, label }))

export default function RoomFormPage() {
  const { roomId, id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!roomId
  const hotelId = isEdit ? null : id

  const [formData, setFormData] = useState({
    hotel_id: hotelId || '',
    room_number: '',
    room_type: 'double',
    description: '',
    price_per_night: '',
    max_occupancy: 2,
    beds: 1,
    amenities: [],
    is_available: true,
    is_active: true
  })
  const [amenities, setAmenities] = useState([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const [fieldErrors, setFieldErrors] = useState({})

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
        // Silent fail
      }
    }
    fetchAmenities()
    return () => { cancelled = true }
  }, [])

  // Fetch room data if editing
  useEffect(() => {
    if (!isEdit) return
    let cancelled = false
    async function fetchRoom() {
      try {
        setLoading(true)
        const data = await apiGet(`/rooms/${roomId}/`)
        if (!cancelled) {
          setFormData({
            hotel_id: data.hotel?.id || '',
            room_number: data.room_number || '',
            room_type: data.room_type || 'double',
            description: data.description || '',
            price_per_night: data.price_per_night !== null && data.price_per_night !== undefined ? String(data.price_per_night) : '',
            max_occupancy: data.max_occupancy || 2,
            beds: data.beds || 1,
            amenities: (data.amenities || []).map(a => a.id),
            is_available: data.is_available !== false,
            is_active: data.is_active !== false
          })
        }
      } catch (err) {
        if (!cancelled) {
          const normalized = normalizeApiError(err)
          setError(normalized.message || 'Impossible de charger la chambre')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    fetchRoom()
    return () => { cancelled = true }
  }, [roomId, isEdit])

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
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

    const errors = {}
    if (!formData.room_number.trim()) errors.room_number = 'Le numéro de chambre est requis'
    if (!formData.price_per_night || isNaN(Number(formData.price_per_night)) || Number(formData.price_per_night) < 0) {
      errors.price_per_night = 'Prix par nuit requis (nombre ≥ 0)'
    }
    if (!formData.max_occupancy || Number(formData.max_occupancy) < 1) {
      errors.max_occupancy = 'Occupation max requise (≥ 1)'
    }
    if (!formData.beds || Number(formData.beds) < 1) {
      errors.beds = 'Nombre de lits requis (≥ 1)'
    }

    if (Object.keys(errors).length > 0) {
      setFieldErrors(errors)
      return
    }

    try {
      setSubmitting(true)
      const payload = {
        hotel_id: Number(formData.hotel_id),
        room_number: formData.room_number.trim(),
        room_type: formData.room_type,
        description: formData.description.trim(),
        price_per_night: Number(formData.price_per_night),
        max_occupancy: Number(formData.max_occupancy),
        beds: Number(formData.beds),
        amenities: formData.amenities,
        is_available: formData.is_available,
        is_active: formData.is_active
      }

      if (isEdit) {
        await apiPatch(`/rooms/${roomId}/`, payload)
        navigate(`/back-office/hotels/${formData.hotel_id}/chambres`, { state: { success: 'Chambre modifiée avec succès' } })
      } else {
        await apiPost('/rooms/', payload)
        navigate(`/back-office/hotels/${hotelId}/chambres`, { state: { success: 'Chambre créée avec succès' } })
      }
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

  const backUrl = isEdit && formData.hotel_id
    ? `/back-office/hotels/${formData.hotel_id}/chambres`
    : hotelId
      ? `/back-office/hotels/${hotelId}/chambres`
      : '/back-office/hotels'

  if (loading) {
    return (
      <div className="manager-page">
        <header className="manager-header">
          <h1>{isEdit ? 'Modifier la chambre' : 'Nouvelle chambre'}</h1>
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
          <h1>{isEdit ? 'Modifier la chambre' : 'Nouvelle chambre'}</h1>
          <p>{isEdit ? 'Mettez à jour les informations de la chambre' : 'Ajoutez une nouvelle chambre à l\'hôtel'}</p>
        </div>
        <Button as={Link} to={backUrl} variant="ghost">
          Annuler
        </Button>
      </header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)} className="alert-fixed">
          {error}
        </Alert>
      )}

      <form className="manager-form" onSubmit={handleSubmit}>
        <section className="manager-form-section" aria-labelledby="info-title">
          <h2 id="info-title" className="manager-form-section-title">Informations de la chambre</h2>
          <div className="manager-form-grid">
            <Input
              label="Numéro de chambre *"
              name="room_number"
              value={formData.room_number}
              onChange={handleChange}
              error={fieldErrors.room_number}
              placeholder="Ex : 101, A-203"
              required
              autoComplete="off"
            />
            <Select
              label="Type de chambre *"
              name="room_type"
              value={formData.room_type}
              onChange={handleChange}
              error={fieldErrors.room_type}
              options={ROOM_TYPE_OPTIONS}
              required
            />
          </div>
          <Textarea
            label="Description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            error={fieldErrors.description}
            placeholder="Description de la chambre, vue, particularités..."
            rows={3}
          />
        </section>

        <section className="manager-form-section" aria-labelledby="capacity-title">
          <h2 id="capacity-title" className="manager-form-section-title">Capacité et tarification</h2>
          <div className="manager-form-grid-3">
            <Input
              label="Prix par nuit *"
              name="price_per_night"
              type="number"
              step="0.01"
              min="0"
              value={formData.price_per_night}
              onChange={handleChange}
              error={fieldErrors.price_per_night}
              placeholder="0.00"
              required
            />
            <Input
              label="Occupation max *"
              name="max_occupancy"
              type="number"
              min="1"
              value={formData.max_occupancy}
              onChange={handleChange}
              error={fieldErrors.max_occupancy}
              placeholder="2"
              required
            />
            <Input
              label="Nombre de lits *"
              name="beds"
              type="number"
              min="1"
              value={formData.beds}
              onChange={handleChange}
              error={fieldErrors.beds}
              placeholder="1"
              required
            />
          </div>
        </section>

        <section className="manager-form-section" aria-labelledby="amenities-title">
          <h2 id="amenities-title" className="manager-form-section-title">Équipements</h2>
          <p className="small muted" style={{ marginBottom: '12px' }}>Sélectionnez les équipements disponibles dans la chambre</p>
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
          <div className="manager-form-grid">
            <Checkbox
              label="Disponible à la réservation"
              name="is_available"
              checked={formData.is_available}
              onChange={handleChange}
              description="La chambre peut être réservée par les clients"
            />
            <Checkbox
              label="Chambre active"
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              description="La chambre existe dans le système (désactivez pour masquer sans supprimer)"
            />
          </div>
        </section>

        <div className="manager-form-actions">
          <Button as={Link} to={backUrl} variant="secondary">Annuler</Button>
          <Button type="submit" variant="primary" loading={submitting}>
            {isEdit ? 'Enregistrer les modifications' : 'Créer la chambre'}
          </Button>
        </div>
      </form>
    </div>
  )
}