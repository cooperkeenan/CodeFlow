import { useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { Alert, Box, Button, Link, Stack, TextField } from '@mui/material'
import AuthLayout from '../components/AuthLayout'
import { forgotPassword } from '../api/auth'

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [sent, setSent] = useState(false)
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await forgotPassword(email)
      setSent(true)
    } catch {
      setError('Could not send the reset email. Please try again.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout title="Reset password" subtitle="We'll email you a reset link">
      {sent ? (
        <Alert severity="success">
          If an account exists for {email}, a reset link is on its way. The link expires in 1 hour.
        </Alert>
      ) : (
        <Box component="form" onSubmit={submit}>
          <Stack spacing={2}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required fullWidth autoFocus />
            <Button type="submit" variant="contained" disabled={busy} fullWidth>
              {busy ? 'Sending…' : 'Send reset link'}
            </Button>
          </Stack>
        </Box>
      )}
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Link component={RouterLink} to="/login" color="text.secondary">Back to sign in</Link>
      </Box>
    </AuthLayout>
  )
}
