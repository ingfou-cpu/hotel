// Constantes partagées pour l'application HotelBooking

export const ROOM_TYPES = {
  single: 'Simple',
  double: 'Double',
  suite: 'Suite',
  family: 'Familiale'
}

export const BOOKING_STATUS = {
  pending: 'En attente',
  confirmed: 'Confirmée',
  cancelled: 'Annulée',
  completed: 'Terminée'
}

export const BOOKING_STATUS_COLORS = {
  pending: 'warning',
  confirmed: 'success',
  cancelled: 'danger',
  completed: 'neutral'
}

export const PAYMENT_STATUS = {
  pending: 'En attente',
  paid: 'Payé',
  failed: 'Échoué',
  refunded: 'Remboursé',
  partially_refunded: 'Remboursement partiel'
}

export const NOTIFICATION_TYPES = {
  info: 'Info',
  booking: 'Réservation',
  payment: 'Paiement',
  cancellation: 'Annulation',
  reminder: 'Rappel'
}

export const USER_ROLES = {
  client: 'Client',
  hotel_manager: 'Gestionnaire',
  admin: 'Administrateur'
}