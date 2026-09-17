// StatusBadge.jsx — Badge de statut avec couleur automatique
// Props: status, type='booking'|'payment', className
import React from 'react'
import Badge from './Badge'
import { BOOKING_STATUS, BOOKING_STATUS_COLORS, PAYMENT_STATUS } from '../lib/constants'

const PAYMENT_STATUS_COLORS = {
  pending: 'warning',
  paid: 'success',
  failed: 'danger',
  refunded: 'neutral',
  partially_refunded: 'info'
}

export default function StatusBadge({ status, type = 'booking', className = '' }) {
  if (!status) return null

  let label = status
  let color = 'neutral'

  if (type === 'booking') {
    label = BOOKING_STATUS[status] || status
    color = BOOKING_STATUS_COLORS[status] || 'neutral'
  } else if (type === 'payment') {
    label = PAYMENT_STATUS[status] || status
    color = PAYMENT_STATUS_COLORS[status] || 'neutral'
  }

  return <Badge color={color} className={className}>{label}</Badge>
}