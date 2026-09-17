// ManagerBookingsPage.jsx — Gestion des réservations (gestionnaire)
import React, { useEffect, useState, useMemo } from 'react'
import { apiGet, apiPost } from '../../lib/api'
import { BOOKING_STATUS, BOOKING_STATUS_COLORS } from '../../lib/constants'
import { formatPrice, formatDate, todayISO } from '../../lib/format'
import Button from '../../components/Button'
import Table from '../../components/Table'
import Pagination from '../../components/Pagination'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import Modal from '../../components/Modal'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import Card from '../../components/Card'
import '../../pages/manager/manager.css'

const STATUS_FILTERS = [
  { value: '', label: 'Toutes' },
  { value: 'pending', label: 'En attente' },
  { value: 'confirmed', label: 'Confirmées' },
  { value: 'cancelled', label: 'Annulées' },
  { value: 'completed', label: 'Terminées' }
]

export default function ManagerBookingsPage() {
  const [bookings, setBookings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageCount, setPageCount] = useState(1)
  const [total, setTotal] = useState(0)
  const [statusFilter, setStatusFilter] = useState('')
  const [actionModal, setActionModal] = useState({ open: false, action: null, booking: null })
  const [actionLoading, setActionLoading] = useState(false)
  const [actionError, setActionError] = useState(null)

  const fetchBookings = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiGet('/bookings/', { status: statusFilter, page })
      setBookings(data.results || [])
      setPageCount(Math.ceil((data.count || 0) / 20) || 1)
      setTotal(data.count || 0)
    } catch (err) {
      setError('Impossible de charger les réservations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchBookings()
  }, [page, statusFilter])

  const handleAction = async (action, booking) => {
    setActionModal({ open: true, action, booking })
    setActionError(null)
  }

  const confirmAction = async () => {
    if (!actionModal.booking || !actionModal.action) return
    try {
      setActionLoading(true)
      const { booking, action } = actionModal
      let endpoint = ''
      switch (action) {
        case 'confirm': endpoint = `/bookings/${booking.id}/confirm/`; break
        case 'cancel': endpoint = `/bookings/${booking.id}/cancel/`; break
        case 'complete': endpoint = `/bookings/${booking.id}/complete/`; break
        default: return
      }
      await apiPost(endpoint, {})
      setActionModal({ open: false, action: null, booking: null })
      fetchBookings()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erreur lors de l\'action'
      setActionError(msg)
    } finally {
      setActionLoading(false)
    }
  }

  const canComplete = (booking) => {
    if (booking.status !== 'confirmed') return false
    const checkOut = new Date(booking.check_out)
    const today = new Date(todayISO())
    today.setHours(0, 0, 0, 0)
    return checkOut <= today
  }

  const columns = useMemo(() => [
    { key: 'booking_code', label: 'Code', render: (row) => <strong>{row.booking_code}</strong> },
    { key: 'client', label: 'Client', render: (row) => row.user?.email || '—' },
    { key: 'hotel', label: 'Hôtel', render: (row) => row.hotel ? `${row.hotel.name} (${row.hotel.city}, ${row.hotel.country})` : '—' },
    { key: 'room', label: 'Chambre', render: (row) => row.room ? `${row.room.room_number} (${row.room.room_type})` : '—' },
    { key: 'dates', label: 'Séjour', render: (row) => `${formatDate(row.check_in)} → ${formatDate(row.check_out)} (${row.nights} nuit${row.nights > 1 ? 's' : ''})` },
    { key: 'total_price', label: 'Total', render: (row) => formatPrice(row.total_price, row.currency || 'EUR'), align: 'right' },
    { key: 'status', label: 'Statut', render: (row) => (
      <StatusBadge status={row.status} type="booking" />
    ), align: 'center' },
    { key: 'actions', label: 'Actions', render: (row) => (
      <div className="manager-table-actions" style={{ gap: '6px' }}>
        {row.status === 'pending' && (
          <>
            <Button variant="primary" size="sm" onClick={() => handleAction('confirm', row)}>Confirmer</Button>
            <Button variant="danger" size="sm" onClick={() => handleAction('cancel', row)}>Annuler</Button>
          </>
        )}
        {row.status === 'confirmed' && (
          <>
            <Button
              variant="success"
              size="sm"
              onClick={() => handleAction('complete', row)}
              disabled={!canComplete(row)}
            >
              Terminer
            </Button>
            {!canComplete(row) && (
              <span className="small muted" style={{ display: 'flex', alignItems: 'center', padding: '0 4px' }}>
                Disponible le {formatDate(row.check_out)}
              </span>
            )}
            <Button variant="danger" size="sm" onClick={() => handleAction('cancel', row)}>Annuler</Button>
          </>
        )}
        {(row.status === 'cancelled' || row.status === 'completed') && (
          <span className="small muted">Aucune action</span>
        )}
      </div>
    ), align: 'right' }
  ], [])

  if (loading && bookings.length === 0) {
    return (
      <div className="manager-page">
        <header className="manager-header">
          <h1>Réservations</h1>
          <p>Gestion des réservations de vos hôtels</p>
        </header>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Spinner size="lg" ariaLabel="Chargement des réservations" />
        </div>
      </div>
    )
  }

  return (
    <div className="manager-page">
      <header className="manager-header">
        <h1>Réservations</h1>
        <p>Gestion des réservations de vos hôtels</p>
      </header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)} className="alert-fixed">
          {error}
        </Alert>
      )}

      <div className="status-tabs" role="tablist" aria-label="Filtrer par statut">
        {STATUS_FILTERS.map(filter => (
          <button
            key={filter.value}
            role="tab"
            aria-selected={statusFilter === filter.value}
            className={`status-tab ${statusFilter === filter.value ? 'active' : ''}`}
            onClick={() => { setStatusFilter(filter.value); setPage(1) }}
          >
            {filter.label}
          </button>
        ))}
      </div>

      <div className="manager-table-container">
        {bookings.length > 0 ? (
          <>
            <Table
              columns={columns}
              rows={bookings}
              emptyMessage="Aucune réservation"
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
            title="Aucune réservation"
            description={statusFilter ? `Aucune réservation avec le statut "${STATUS_FILTERS.find(f => f.value === statusFilter)?.label}"` : 'Aucune réservation pour vos hôtels pour le moment.'}
            icon={<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true"><rect x="8" y="10" width="32" height="28" rx="3" stroke="currentColor" strokeWidth="1.5"/><path d="M24 10V6M24 38v4M10 24H6M42 24h4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><path d="M14 18h20M14 24h14M14 30h10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>}
          />
        )}
      </div>

      <Modal
        open={actionModal.open}
        onClose={() => { setActionModal({ open: false, action: null, booking: null }); setActionError(null) }}
        title={actionModal.action === 'confirm' ? 'Confirmer la réservation' : actionModal.action === 'cancel' ? 'Annuler la réservation' : 'Terminer la réservation'}
        size="sm"
      >
        {actionModal.booking && (
          <div>
            <p>Confirmez-vous cette action pour la réservation <strong>{actionModal.booking.booking_code}</strong> ?</p>
            {actionModal.action === 'cancel' && (
              <p className="small muted">L'annulation déclenchera un remboursement automatique si la réservation a été payée.</p>
            )}
            {actionModal.action === 'complete' && (
              <p className="small muted">La réservation sera marquée comme terminée. Cette action est irréversible.</p>
            )}
            {actionError && <Alert type="error">{actionError}</Alert>}
            <div className="modal-footer">
              <Button variant="secondary" onClick={() => { setActionModal({ open: false, action: null, booking: null }); setActionError(null) }}>Annuler</Button>
              <Button
                variant={actionModal.action === 'cancel' ? 'danger' : actionModal.action === 'confirm' ? 'primary' : 'success'}
                loading={actionLoading}
                onClick={confirmAction}
              >
                {actionModal.action === 'confirm' ? 'Confirmer' : actionModal.action === 'cancel' ? 'Annuler' : 'Terminer'}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}