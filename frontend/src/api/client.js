import { API_URL } from '../constants'
import { getSessionToken } from './session'

export async function request(path, options = {}) {
  const token = getSessionToken()
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  })
  if (!res.ok) {
    const text = await res.text()
    let detail = null
    try { detail = JSON.parse(text)?.detail ?? null } catch { detail = null }
    const error = new Error(detail || `${res.status}: ${text}`)
    error.status = res.status
    error.detail = detail
    throw error
  }
  if (res.status === 204) return null
  return res.json()
}
