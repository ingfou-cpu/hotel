// ManagerPaymentsPage.jsx — Gestion des paiements (gestionnaire)
import React, { useEffect, useState, useMemo } from 'react'
import { apiGet, apiPost } from '../../lib/api'
import { PAYMENT_STATUS } from '../../lib/constants'
import { formatPrice, formatDateTime } from '../../lib/format'
import Button from '../../components/Button'
import Table from '../../components/Table'
import Pagination from '../../components/Pagination'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import Badge from '../../components/Badge'
import Modal from '../../components/Modal'
import StatusBadge from '../../components/StatusBadge'
import EmptyState from '../../components/EmptyState'
import '../../pages/manager/manager.css'

export default function ManagerPaymentsPage() {
  const [payments, setPayments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [pageCount, setPageCount] = useState(1)
  const [total, setTotal] = useState(0)
  const [refundModal, setRefundModal] = useState({ open: false, payment: null })
  const [refundLoading, setRefundLoading] = useState(false)
  const [refundError, setRefundError] = useState(null)

  const fetchPayments = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiGet('/payments/', { page })
      setPayments(data.results || [])
      setPageCount(Math.ceil((data.count || 0) / 20) || 1)
      setTotal(data.count || 0)
    } catch (err) {
      setError('Impossible de charger les paiements')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPayments()
  }, [page])

  const handleRefund = (payment) => {
    setRefundModal({ open: true, payment })
    setRefundError(null)
  }

  const confirmRefund = async () => {
    if (!refundModal.payment) return
    try {
      setRefundLoading(true)
      await apiPost(`/payments/${refundModal.payment.id}/refund/`, {})
      setRefundModal({ open: false, payment: null })
      fetchPayments()
    } catch (err) {
      const msg = err.response?.data?.detail || 'Erreur lors du remboursement'
      setRefundError(msg)
    } finally {
      setRefundLoading(false)
    }
  }

  const columns = useMemo(() => [
    { key: 'booking_code', label: 'Réservation', render: (row) => <strong>{row.booking_code}</strong> },
    { key: 'user_email', label: 'Client', render: (row) => row.user_email || '—' },
    { key: 'amount', label: 'Montant', render: (row) => formatPrice(row.amount, row.currency || 'EUR'), align: 'right' },
    { key: 'status', label: 'Statut', render: (row) => (
      <StatusBadge status={row.status} type="payment" />
    ), align: 'center' },
    { key: 'payment_method', label: 'Moyen', render: (row) => (
      <Badge color="neutral" style={{ textTransform: 'capitalize' }}>{row.payment_method || '—'}</Badge>
    ), align: 'center' },
    { key: 'created_at', label: 'Créé le', render: (row) => formatDateTime(row.created_at), align: 'center' },
    { key: 'actions', label: 'Actions', render: (row) => (
      <div className="manager-table-actions">
        {row.status === 'paid' && (
          <Button variant="warning" size="sm" onClick={() => handleRefund(row)}>Rembourser</Button>
        )}
        {row.status !== 'paid' && <span className="small muted">—</span>}
      </div>
    ), align: 'right' }
  ], [])

  if (loading && payments.length === 0) {
    return (
      <div className="manager-page">
        <header className="manager-header">
          <h1>Paiements</h1>
          <p>Gestion des paiements des réservations de vos hôtels</p>
        </header>
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Spinner size="lg" ariaLabel="Chargement des paiements" />
        </div>
      </div>
    )
  }

  return (
    <div className="manager-page">
      <header className="manager-header">
        <h1>Paiements</h1>
        <p>Gestion des paiements des réservations de vos hôtels</p>
      </header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)} className="alert-fixed">
          {error}
        </Alert>
      )}

      <div className="manager-table-container">
        {payments.length > 0 ? (
          <>
            <Table
              columns={columns}
              rows={payments}
              emptyMessage="Aucun paiement"
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
            title="Aucun paiement"
            description="Aucun paiement enregistré pour les réservations de vos hôtels."
            icon={<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true"><rect x="10" y="12" width="28" height="18" rx="3" stroke="currentColor" strokeWidth="1.5"/><path d="M14 12V8M34 12v4M14 30h20" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/><circle cx="24" cy="22" r="4" stroke="currentColor" strokeWidth="1.5"/></svg>}
          />
        )}
      </div>

      <Modal
        open={refundModal.open}
        onClose={() => { setRefundModal({ open: false, payment: null }); setRefundError(null) }}
        title="Rembourser le paiement"
        size="sm"
      >
        {refundModal.payment && (
          <div className="refund-modal-content">
            <p>Confirmez-vous le remboursement intégral pour la réservation <strong>{refundModal.payment.booking_code}</strong> ?</p>
            <div className="refund-modal-amount">
              {formatPrice(refundModal.payment.amount, refundModal.payment.currency || 'EUR')}
            </div>
            <p className="small muted">Cette action est irréversible. Le montant sera remboursé sur le moyen de paiement d'origine.</p>
            {refundError && <Alert type="error">{refundError}</Alert>}
            <div className="modal-footer">
              <Button variant="secondary" onClick={() => { setRefundModal({ open: false, payment: null }); setRefundError(null) }}>Annuler</Button>
              <Button variant="danger" loading={refundLoading} onClick={confirmRefund}>Rembourser</Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  )
}