// Instance Axios + gestion JWT pour HotelBooking
import axios from 'axios'

const TOKEN_KEYS = {
  access: 'hb_access',
  refresh: 'hb_refresh'
}

let inMemoryTokens = {
  access: null,
  refresh: null
}

let authFailureHandler = null
let isRefreshing = false
let refreshPromise = null

function getStoredTokens() {
  if (inMemoryTokens.access) return inMemoryTokens
  const access = localStorage.getItem(TOKEN_KEYS.access)
  const refresh = localStorage.getItem(TOKEN_KEYS.refresh)
  if (access && refresh) {
    inMemoryTokens = { access, refresh }
  }
  return inMemoryTokens
}

function setTokens(access, refresh) {
  inMemoryTokens = { access, refresh }
  localStorage.setItem(TOKEN_KEYS.access, access)
  localStorage.setItem(TOKEN_KEYS.refresh, refresh)
}

function clearTokens() {
  inMemoryTokens = { access: null, refresh: null }
  localStorage.removeItem(TOKEN_KEYS.access)
  localStorage.removeItem(TOKEN_KEYS.refresh)
}

export function setAuthFailureHandler(fn) {
  authFailureHandler = fn
}

function triggerAuthFailure() {
  clearTokens()
  if (authFailureHandler) {
    authFailureHandler()
  } else {
    window.location.assign('/connexion')
  }
}

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

const rawApi = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' }
})

const noAuthUrls = [
  '/auth/login/',
  '/auth/register/',
  '/auth/refresh/',
  '/auth/change-password/'
]

api.interceptors.request.use((config) => {
  const { access } = getStoredTokens()
  if (access) {
    config.headers.Authorization = `Bearer ${access}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    const status = error.response?.status

    if (
      status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !noAuthUrls.some(url => originalRequest.url?.includes(url))
    ) {
      originalRequest._retry = true

      if (isRefreshing) {
        try {
          await refreshPromise
          const { access } = getStoredTokens()
          if (access) {
            originalRequest.headers.Authorization = `Bearer ${access}`
          }
          return api(originalRequest)
        } catch {
          return Promise.reject(error)
        }
      }

      isRefreshing = true
      const { refresh } = getStoredTokens()

      refreshPromise = (async () => {
        try {
          const response = await rawApi.post('/auth/refresh/', { refresh })
          const { access: newAccess, refresh: newRefresh } = response.data
          setTokens(newAccess, newRefresh)
          return newAccess
        } catch (err) {
          triggerAuthFailure()
          throw err
        } finally {
          isRefreshing = false
          refreshPromise = null
        }
      })()

      try {
        await refreshPromise
        const { access } = getStoredTokens()
        if (access) {
          originalRequest.headers.Authorization = `Bearer ${access}`
        }
        return api(originalRequest)
      } catch {
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  }
)

export function apiGet(url, params) {
  return api.get(url, { params }).then(r => r.data)
}

export function apiPost(url, data) {
  return api.post(url, data).then(r => r.data)
}

export function apiPatch(url, data) {
  return api.patch(url, data).then(r => r.data)
}

export function apiDelete(url) {
  return api.delete(url).then(r => r.data)
}

export function normalizeApiError(error) {
  const result = { message: '', fieldErrors: null }

  if (!error.response) {
    result.message = 'Impossible de contacter le serveur'
    return result
  }

  const data = error.response.data
  const status = error.response.status

  if (typeof data === 'string') {
    result.message = data
    return result
  }

  if (data?.detail) {
    result.message = data.detail
    return result
  }

  if (data?.non_field_errors) {
    result.message = Array.isArray(data.non_field_errors)
      ? data.non_field_errors[0]
      : data.non_field_errors
    return result
  }

  if (typeof data === 'object' && data !== null) {
    const fieldErrors = {}
    let firstMessage = null

    for (const [field, messages] of Object.entries(data)) {
      if (Array.isArray(messages) && messages.length > 0) {
        fieldErrors[field] = messages[0]
        if (!firstMessage) firstMessage = messages[0]
      } else if (typeof messages === 'string') {
        fieldErrors[field] = messages
        if (!firstMessage) firstMessage = messages
      }
    }

    if (Object.keys(fieldErrors).length > 0) {
      result.fieldErrors = fieldErrors
      result.message = firstMessage || 'Erreur de validation'
      return result
    }
  }

  result.message = `Erreur ${status}: ${error.message || 'Inconnue'}`
  return result
}

export { rawApi }