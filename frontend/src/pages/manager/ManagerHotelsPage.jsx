// ManagerHotelsPage.jsx — Liste des hôtels (gestionnaire)
import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiGet, apiDelete } from '../../lib/api'
import { useAuth, isManagerOrStaff } from '../../lib/auth'
import { formatPrice } from '../../lib/format'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Badge from '../../components/Badge'
import Table from '../../components/Table'
import Pagination from '../../components/Pagination'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import Modal from '../../components/Modal'
import EmptyState from '../../components/EmptyState'
import HotelCard from '../../components/HotelCard'
import '../../pages/manager/manager.css'

export default function ManagerHotelsPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageCount, setPageCount] = useState(1)
  const [total, setTotal] = useState(0)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [hotelToDelete, setHotelToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState(null)

  const canCreateHotel = user && isManagerOrStaff(user)

  useEffect(() => {
    let cancelled = false

    async function fetchHotels() {
      try {
        setLoading(true)
        setError(null)
        const data = await apiGet('/hotels/mine/', { page })
        if (!cancelled) {
          setHotels(data.results || [])
          setPageCount(Math.ceil((data.count || 0) / 20) || 1)
          setTotal(data.count || 0)
        }
      } catch (err) {
        if (!cancelled) {
          setError('Impossible de charger la liste des hôtels')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchHotels()
    return () => { cancelled = true }
  }, [page])

  const handleDelete = async () => {
    if (!hotelToDelete) return
    try {
      setDeleting(true)
      setDeleteError(null)
      await apiDelete(`/hotels/${hotelToDelete.id}/`)
      setDeleteModalOpen(false)
      setHotelToDelete(null)
      // Refresh current page, or go back if last item on last page
      if (hotels.length === 1 && page > 1) {
        setPage(page - 1)
      } else {
        // Trigger refetch by setting a key or just let the effect run
        setHotels(prev => prev.filter(h => h.id !== hotelToDelete.id))
      }
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Erreur lors de la suppression')
    } finally {
      setDeleting(false)
    }
  }

  const columns = [
    { key: 'image', label: '', render: (row) => (
      row.image ? (
        <img src={row.image} alt="" className="hotel-image-thumb" loading="lazy" />
      ) : (
        <div className="hotel-image-placeholder">Pas d'image</div>
      )
    ), align: 'center', width: '72px' },
    { key: 'name', label: 'Hôtel', render: (row) => (
      <div>
        <div style={{ fontWeight: 600, color: 'var(--color-text)' }}>{row.name}</div>
        <div className="small muted">{row.city}{row.country ? `, ${row.country}` : ''}</div>
      </div>
    ) },
    { key: 'stars', label: 'Étoiles', render: (row) => (
      row.stars ? '★'.repeat(row.stars) + (row.stars > 1 ? 's' : '') : '—'
    ), align: 'center' },
    { key: 'starting_price', label: 'Prix départ', render: (row) => row.starting_price ? formatPrice(row.starting_price) : '—', align: 'right' },
    { key: 'room_count', label: 'Chambres', render: (row) => row.room_count || 0, align: 'center' },
    { key: 'average_rating', label: 'Note', render: (row) => row.average_rating ? `${Number(row.average_rating).toFixed(1)} (${row.reviews_count || 0})` : '—', align: 'center' },
    { key: 'is_active', label: 'Statut', render: (row) => (
      <Badge color={row.is_active ? 'success' : 'neutral'}>
        {row.is_active ? 'Actif' : 'Inactif'}
      </Badge>
    ), align: 'center' },
    { key: 'actions', label: 'Actions', render: (row) => (
      <div className="manager-table-actions">
        <Button as={Link} to={`/back-office/hotels/${row.id}/modifier`} variant="ghost" size="sm">Modifier</Button>
        <Button as={Link} to={`/back-office/hotels/${row.id}/chambres`} variant="ghost" size="sm">Chambres</Button>
        <Button variant="danger" size="sm" onClick={() => { setHotelToDelete(row); setDeleteModalOpen(true) }}>Supprimer</Button>
      </div>
    ), align: 'right' }
  ]

  if (loading && hotels.length === 0) {
    return (
      <div className="manager-page">
        <header className="manager-header">
          <div>
            <h1>Mes hôtels</h1>
            <p>Liste de vos hôtels avec actions de gestion</p>
          </div>
          {canCreateHotel && (
            <Button as={Link} to="/back-office/hotels/nouveau" variant="primary">
              Nouvel hôtel
            </Button>
          )}
        </header>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Spinner size="lg" ariaLabel="Chargement des hôtels" />
        </div>
      </div>
    )
  }

  return (
    <div className="manager-page">
      <header className="manager-header">
        <div>
          <h1>Mes hôtels</h1>
          <p>Liste de vos hôtels avec actions de gestion</p>
        </div>
        {canCreateHotel && (
          <Button as={Link} to="/back-office/hotels/nouveau" variant="primary">
            Nouvel hôtel
          </Button>
        )}
      </header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)} className="alert-fixed">
          {error}
        </Alert>
      )}

      {!canCreateHotel && (
        <Alert type="warning" className="alert-fixed" style={{ maxWidth: '600px' }}>
          Votre rôle ne permet pas la création d'hôtels. Contactez un administrateur si nécessaire.
        </Alert>
      )}

      <div className="manager-table-container">
        {hotels.length > 0 ? (
          <>
            <Table
              columns={columns}
              rows={hotels}
              emptyMessage="Aucun hôtel"
              hoverable
            />
            <Pagination
              page={page}
              pageCount={pageCount}
              total={total}
              onChange={setPage}
              showInfo
            />
          </>
        ) : (
          <EmptyState
            title="Aucun hôtel"
            description="Vous n'avez pas encore d'hôtel. Commencez par en créer un."
            action={canCreateHotel && <Button as={Link} to="/back-office/hotels/nouveau" variant="primary">Créer un hôtel</Button>}
            icon={<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true"><rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="1.5"/><path d="M24 10V6M24 38v4M10 24H6M42 24h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>}
          />
        )}
      </div>

      <Modal
        open={deleteModalOpen}
        onClose={() => { setDeleteModalOpen(false); setHotelToDelete(null); setDeleteError(null) }}
        title="Supprimer l'hôtel"
        size="sm"
      >
        {hotelToDelete && (
          <div>
            <p>Êtes-vous sûr de vouloir supprimer <strong>{hotelToDelete.name}</strong> ?</p>
            <p className="small muted">Cette action est irréversible et supprimera aussi toutes les chambres associées.</p>
            {deleteError && <Alert type="error">{deleteError}</Alert>}
            <div className="modal-footer">
              <Button variant="secondary" onClick={() => { setDeleteModalOpen(false); setHotelToDelete(null); setDeleteError(null) }}>Annuler</Button>
              <Button variant="danger" loading={deleting} onClick={handleDelete}>Supprimer</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}