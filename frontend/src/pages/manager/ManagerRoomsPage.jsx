// ManagerRoomsPage.jsx — Liste des chambres d'un hôtel
import React, { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { apiGet, apiDelete } from '../../lib/api'
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
import '../../pages/manager/manager.css'

export default function ManagerRoomsPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [hotel, setHotel] = useState(null)
  const [rooms, setRooms] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageCount, setPageCount] = useState(1)
  const [total, setTotal] = useState(0)
  const [deleteModalOpen, setDeleteModalOpen] = useState(false)
  const [roomToDelete, setRoomToDelete] = useState(null)
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState(null)

  // Fetch hotel info
  useEffect(() => {
    let cancelled = false
    async function fetchHotel() {
      try {
        const data = await apiGet(`/hotels/${id}/`)
        if (!cancelled) {
          setHotel(data)
        }
      } catch {
        // Silently fail - hotel name is optional for the page
      }
    }
    fetchHotel()
    return () => { cancelled = true }
  }, [id])

  // Fetch rooms
  useEffect(() => {
    let cancelled = false
    async function fetchRooms() {
      try {
        setLoading(true)
        setError(null)
        const data = await apiGet('/rooms/', { hotel: id, page })
        if (!cancelled) {
          setRooms(data.results || [])
          setPageCount(Math.ceil((data.count || 0) / 20) || 1)
          setTotal(data.count || 0)
        }
      } catch (err) {
        if (!cancelled) {
          setError('Impossible de charger la liste des chambres')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }
    fetchRooms()
    return () => { cancelled = true }
  }, [id, page])

  const handleDelete = async () => {
    if (!roomToDelete) return
    try {
      setDeleting(true)
      setDeleteError(null)
      await apiDelete(`/rooms/${roomToDelete.id}/`)
      setDeleteModalOpen(false)
      setRoomToDelete(null)
      if (rooms.length === 1 && page > 1) {
        setPage(page - 1)
      } else {
        setRooms(prev => prev.filter(r => r.id !== roomToDelete.id))
      }
    } catch (err) {
      setDeleteError(err.response?.data?.detail || 'Erreur lors de la suppression')
    } finally {
      setDeleting(false)
    }
  }

  const columns = [
    { key: 'room_number', label: 'Numéro', render: (row) => <strong>{row.room_number}</strong> },
    { key: 'room_type_display', label: 'Type', render: (row) => row.room_type_display || row.room_type },
    { key: 'price_per_night', label: 'Prix/nuit', render: (row) => formatPrice(row.price_per_night), align: 'right' },
    { key: 'max_occupancy', label: 'Occup. max', render: (row) => row.max_occupancy, align: 'center' },
    { key: 'beds', label: 'Lits', render: (row) => row.beds, align: 'center' },
    { key: 'is_available', label: 'Disponible', render: (row) => (
      <Badge color={row.is_available ? 'success' : 'neutral'}>{row.is_available ? 'Oui' : 'Non'}</Badge>
    ), align: 'center' },
    { key: 'is_active', label: 'Actif', render: (row) => (
      <Badge color={row.is_active ? 'success' : 'neutral'}>{row.is_active ? 'Oui' : 'Non'}</Badge>
    ), align: 'center' },
    { key: 'actions', label: 'Actions', render: (row) => (
      <div className="manager-table-actions">
        <Button as={Link} to={`/back-office/chambres/${row.id}/modifier`} variant="ghost" size="sm">Modifier</Button>
        <Button variant="danger" size="sm" onClick={() => { setRoomToDelete(row); setDeleteModalOpen(true) }}>Supprimer</Button>
      </div>
    ), align: 'right' }
  ]

  if (loading && rooms.length === 0) {
    return (
      <div className="manager-page">
        <header className="manager-header">
          <div>
            <h1>Chambres</h1>
            <p>{hotel?.name || `Hôtel #${id}`}</p>
          </div>
          <Button as={Link} to={`/back-office/hotels/${id}/chambres/nouveau`} variant="primary">
            Nouvelle chambre
          </Button>
        </header>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Spinner size="lg" ariaLabel="Chargement des chambres" />
        </div>
      </div>
    )
  }

  return (
    <div className="manager-page">
      <header className="manager-header">
        <div>
          <h1>Chambres</h1>
          <p>
            <Link to="/back-office/hotels" className="muted" style={{ textDecoration: 'underline' }}>
              ← Retour aux hôtels
            </Link>
            {hotel && <span style={{ marginLeft: 8 }}> — {hotel.name}</span>}
          </p>
        </div>
        <Button as={Link} to={`/back-office/hotels/${id}/chambres/nouveau`} variant="primary">
          Nouvelle chambre
        </Button>
      </header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)} className="alert-fixed">
          {error}
        </Alert>
      )}

      <div className="manager-table-container">
        {rooms.length > 0 ? (
          <>
            <Table
              columns={columns}
              rows={rooms}
              emptyMessage="Aucune chambre"
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
            title="Aucune chambre"
            description="Cet hôtel n'a pas encore de chambres. Ajoutez la première chambre pour commencer."
            action={<Button as={Link} to={`/back-office/hotels/${id}/chambres/nouveau`} variant="primary">Créer une chambre</Button>}
            icon={<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true"><rect x="6" y="10" width="36" height="28" rx="4" stroke="currentColor" strokeWidth="1.5"/><path d="M24 10V6M24 38v4M10 24H6M42 24h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>}
          />
        )}
      </div>

      <Modal
        open={deleteModalOpen}
        onClose={() => { setDeleteModalOpen(false); setRoomToDelete(null); setDeleteError(null) }}
        title="Supprimer la chambre"
        size="sm"
      >
        {roomToDelete && (
          <div>
            <p>Êtes-vous sûr de vouloir supprimer la chambre <strong>{roomToDelete.room_number}</strong> ?</p>
            <p className="small muted">Cette action est irréversible.</p>
            {deleteError && <Alert type="error">{deleteError}</Alert>}
            <div className="modal-footer">
              <Button variant="secondary" onClick={() => { setDeleteModalOpen(false); setRoomToDelete(null); setDeleteError(null) }}>Annuler</Button>
              <Button variant="danger" loading={deleting} onClick={handleDelete}>Supprimer</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}