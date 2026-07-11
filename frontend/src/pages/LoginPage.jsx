import { useState } from 'react'
import { Link as RouterLink, useNavigate } from 'react-router-dom'
import { Alert, Box, Button, Divider, Link, Stack, TextField } from '@mui/material'
import GitHubIcon from '@mui/icons-material/GitHub'
import AuthLayout from '../components/AuthLayout'
import { login } from '../api/auth'
import { startGithubOAuth } from '../api/github'
import { saveSession } from '../api/session'

export default function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      const d = await login(email, password)
      saveSession(d.session_token, d.user)
      navigate('/')
    } catch (err) {
      setError('Invalid email or password')
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthLayout title="Sign in" subtitle="Welcome back to CodeFlow">
      <Box component="form" onSubmit={submit}>
        <Stack spacing={2}>
          {error && <Alert severity="error">{error}</Alert>}
          <TextField label="Email" type="email" value={email} onChange={e => setEmail(e.target.value)} required fullWidth autoFocus />
          <TextField label="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} required fullWidth />
          <Button type="submit" variant="contained" disabled={busy} fullWidth>Sign in</Button>
        </Stack>
      </Box>
      <Divider sx={{ my: 2 }}>or</Divider>
      <Button variant="outlined" color="secondary" startIcon={<GitHubIcon />} onClick={startGithubOAuth} fullWidth>
        Sign in with GitHub
      </Button>
      <Box sx={{ mt: 2, textAlign: 'center' }}>
        <Link component={RouterLink} to="/signup" color="text.secondary">No account? Create one</Link>
      </Box>
    </AuthLayout>
  )
}
