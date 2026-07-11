import { Navigate } from 'react-router-dom'
import { getSessionToken } from '../api/session'

export default function RequireAuth({ children }) {
  if (!getSessionToken()) return <Navigate to="/login" replace />
  return children
}
