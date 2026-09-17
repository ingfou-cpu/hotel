// Helpers de formatage français pour l'application HotelBooking

const frNumberFormat = new Intl.NumberFormat('fr-FR', {
  style: 'currency',
  currency: 'EUR',
  currencyDisplay: 'narrowSymbol'
})

const frDateFormat = new Intl.DateTimeFormat('fr-FR', {
  day: 'numeric',
  month: 'short',
  year: 'numeric'
})

const frDateTimeFormat = new Intl.DateTimeFormat('fr-FR', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit'
})

export function formatPrice(value, currency = 'EUR') {
  if (value === null || value === undefined || value === '') return ''
  const num = typeof value === 'string' ? parseFloat(value) : value
  if (isNaN(num)) return ''
  try {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency,
      currencyDisplay: 'narrowSymbol'
    }).format(num)
  } catch {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency,
      currencyDisplay: 'symbol'
    }).format(num)
  }
}

export function formatDate(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  if (isNaN(date.getTime())) return ''
  return frDateFormat.format(date)
}

export function formatDateTime(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  if (isNaN(date.getTime())) return ''
  return frDateTimeFormat.format(date)
}

export function nightsBetween(checkIn, checkOut) {
  if (!checkIn || !checkOut) return 0
  const start = new Date(checkIn)
  const end = new Date(checkOut)
  if (isNaN(start.getTime()) || isNaN(end.getTime())) return 0
  const diffMs = end.getTime() - start.getTime()
  return Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)))
}

export function todayISO() {
  const now = new Date()
  return now.toISOString().split('T')[0]
}

export function toISODate(dateStr) {
  if (!dateStr) return ''
  if (dateStr instanceof Date) {
    return dateStr.toISOString().split('T')[0]
  }
  const date = new Date(dateStr)
  if (isNaN(date.getTime())) return ''
  return date.toISOString().split('T')[0]
}

export function validateDateRange(checkIn, checkOut) {
  if (!checkIn || !checkOut) return 'Les dates d\'arrivée et de départ sont requises'
  const start = new Date(checkIn)
  const end = new Date(checkOut)
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  if (isNaN(start.getTime()) || isNaN(end.getTime())) {
    return 'Format de date invalide'
  }

  if (start < today) {
    return 'La date d\'arrivée ne peut pas être dans le passé'
  }

  if (end <= start) {
    return 'La date de départ doit être postérieure à la date d\'arrivée'
  }

  return null
}