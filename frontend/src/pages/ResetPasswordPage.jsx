import { useState } from 'react'
import { Link as RouterLink, useNavigate, useSearchParams } from 'react-router-dom'
import { Alert, Box, Button, Link, Stack, TextField } from '@mui/material'
import AuthLayout from '../components/AuthLayout'
import { resetPassword } from '../api/auth'

const MIN_LENGTH = 8

export default function ResetPasswordPage() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const token = params.get('token') || ''
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (password !== confirm) {
      setError('Passwords do not match')
      return
    }
    setBusy(true)
    try {
      await resetPassword(token, password)
      navigate('/login')
    } catch {
      setError('This reset link is invalid or has expired. Request a new one.')
    } finally {
      setBusy(false)
    }
  }

  if (!token) {
    return (
      <AuthLayout title="Reset password" subtitle="Choose a new password">
        <Alert severity="error">This reset link is missing its token.</Alert>
        <Box sx={{ mt: 2, textAlign: 'center' }}>
          <Link component={RouterLink} to="/forgot-password" color="text.secondary">Request a new link</Link>
        </Box>
      </AuthLayout>
    )
  }

  return (
    <AuthLayout title="Reset password" subtitle="Choose a new password">
      <Box component="form" onSubmit={submit}>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField
            label="New password"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            fullWidth
            autoFocus
            inputProps={{ minLength: MIN_LENGTH }}
            helperText={`At least ${MIN_LENGTH} characters`}
          />
          <TextField label="Confirm password" type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required fullWidth />
          <Button type="submit" variant="contained" disabled={busy} fullWidth>
            {busy ? 'Saving…' : 'Set new password'}
          </Button>
        </Stack>
      </Box>
    </AuthLayout>
  )
}
