// DashboardPage.jsx — Tableau de bord gestionnaire
import React, { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiGet } from '../../lib/api'
import { useAuth } from '../../lib/auth'
import { formatPrice } from '../../lib/format'
import Card from '../../components/Card'
import Button from '../../components/Button'
import Spinner from '../../components/Spinner'
import Alert from '../../components/Alert'
import EmptyState from '../../components/EmptyState'
import '../../pages/manager/manager.css'

function StatCard({ label, value, hint, icon }) {
  return (
    <Card className="stat-card">
      <div className="stat-card-label">{label}</div>
      <div className="stat-card-value">{value}</div>
      {hint && <div className="stat-card-hint">{hint}</div>}
    </Card>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState({
    hotels: 0,
    pendingBookings: 0,
    confirmedBookings: 0,
    totalBookings: 0,
    recentPayments: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function fetchStats() {
      try {
        setLoading(true)
        setError(null)

        const [hotelsRes, pendingBookingsRes, confirmedBookingsRes, allBookingsRes, paymentsRes] = await Promise.all([
          apiGet('/hotels/mine/'),
          apiGet('/bookings/', { status: 'pending', page: 1 }),
          apiGet('/bookings/', { status: 'confirmed', page: 1 }),
          apiGet('/bookings/', { page: 1 }),
          apiGet('/payments/', { page: 1 })
        ])

        if (!cancelled) {
          setStats({
            hotels: hotelsRes.count || 0,
            pendingBookings: pendingBookingsRes.count || 0,
            confirmedBookings: confirmedBookingsRes.count || 0,
            totalBookings: allBookingsRes.count || 0,
            recentPayments: paymentsRes.count || 0
          })
        }
      } catch (err) {
        if (!cancelled) {
          setError('Impossible de charger les statistiques')
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    fetchStats()
    return () => { cancelled = true }
  }, [])

  if (loading) {
    return (
      <div className="manager-page">
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
          <Spinner size="lg" ariaLabel="Chargement du tableau de bord" />
        </div>
      </div>
    )
  }

  return (
    <div className="manager-page">
      <header className="manager-header">
        <div>
          <h1>Tableau de bord</h1>
          <p>Bonjour, {user?.full_name || user?.first_name || 'Gestionnaire'}</p>
        </div>
      </header>

      {error && (
        <Alert type="error" dismissible onDismiss={() => setError(null)} className="alert-fixed">
          {error}
        </Alert>
      )}

      <div className="manager-stats" role="region" aria-label="Statistiques principales">
        <StatCard label="Mes hôtels" value={stats.hotels} hint="Hôtels gérés" />
        <StatCard label="Réservations en attente" value={stats.pendingBookings} hint="Nécessitent une action" />
        <StatCard label="Réservations confirmées" value={stats.confirmedBookings} hint="À venir ou en cours" />
        <StatCard label="Total réservations" value={stats.totalBookings} hint="Toutes statuts confondus" />
        <StatCard label="Paiements récents" value={stats.recentPayments} hint="Page 1 — tous statuts" />
      </div>

      <section aria-labelledby="quick-access-title">
        <h2 id="quick-access-title" className="manager-form-section-title">Accès rapide</h2>
        <div className="manager-actions">
          <Button as={Link} to="/back-office/hotels" variant="primary">
            Gérer mes hôtels
          </Button>
          <Button as={Link} to="/back-office/reservations" variant="secondary">
            Voir les réservations
          </Button>
          <Button as={Link} to="/back-office/paiements" variant="secondary">
            Voir les paiements
          </Button>
          <Button as={Link} to="/back-office/hotels/nouveau" variant="ghost">
            Nouvel hôtel
          </Button>
        </div>
      </section>

      <section aria-labelledby="recent-activity-title">
        <h2 id="recent-activity-title" className="manager-form-section-title">Activité récente</h2>
        <Card>
          <EmptyState
            title="Aucune activité récente"
            description="Les statistiques ci-dessus reflètent l'état actuel de vos hôtels et réservations."
            icon={<svg width="48" height="48" viewBox="0 0 48 48" fill="none" aria-hidden="true"><circle cx="24" cy="24" r="20" stroke="currentColor" strokeWidth="1.5"/><path d="M24 14v10l7 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>}
          />
        </Card>
      </section>
    </div>
  )
}