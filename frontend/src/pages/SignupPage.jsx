import { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Link, Stack, TextField } from '@mui/material'
import AuthLayout from '../components/AuthLayout'
import { signup } from '../api/auth'
import { saveSession } from '../api/session'

export default function SignupPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    if (password !== confirm) { setError('Passwords do not match'); return }
    setBusy(true)
    try {
      const d = await signup(email, password)
      saveSession(d.session_token, d.user)
      navigate('/')
    } catch (err) {
      setError(err.message.includes('409') ? 'Email already registered' : 'Could not create account')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout title="Create account" subtitle="Sign up with email and password">
      <Box component="form" onSubmit={submit}>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required fullWidth autoFocus />
          <TextField label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required fullWidth />
          <TextField label="Confirm password" type="password" value={confirm} onChange={e => setConfirm(e.target.value)} required fullWidth />
          <Button type="submit" variant="contained" disabled={busy} fullWidth>Create account</Button>
        </Stack>
      </Box>
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Link component={RouterLink} to="/login" color="text.secondary">Already have an account? Sign in</Link>
      </Box>
    </AuthLayout>
  )
}
