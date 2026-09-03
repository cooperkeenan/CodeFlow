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
    const error = new Error(`${res.status}: ${text}`)
    error.status = res.status
    throw error
  }
  if (res.status === 204) return null
  return res.json()
}
