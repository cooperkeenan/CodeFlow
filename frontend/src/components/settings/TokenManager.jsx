import { useEffect, useState } from 'react'
import { Alert, Box, Button, Paper, Stack, TextField, Typography } from '@mui/material'
import { createToken, listTokens, revokeToken } from '../../api/tokens'

export default function TokenManager() {
  const [tokens, setTokens] = useState([])
  const [name, setName] = useState('')
  const [newToken, setNewToken] = useState(null)
  const [error, setError] = useState(null)

  const refresh = () => listTokens().then(setTokens).catch(e => setError(e.message))
  useEffect(() => { refresh() }, [])

  const create = () => {
    if (!name.trim()) return
    createToken(name.trim())
      .then(t => { setNewToken(t); setName(''); refresh() })
      .catch(e => setError(e.message))
  }

  const revoke = (id) => revokeToken(id).then(refresh).catch(e => setError(e.message))

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>API tokens</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        Use an API token to run CodeFlow from CI.
      </Typography>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {newToken && (
        <Alert severity="success" sx={{ mb: 2, wordBreak: 'break-all' }}>
          Copy now — shown once: <code>{newToken.token}</code>
        </Alert>
      )}
      <Stack direction="row" spacing={1} sx={{ mb: 2 }}>
        <TextField size="small" placeholder="Token name (e.g. ci)" value={name} onChange={e => setName(e.target.value)} />
        <Button variant="contained" onClick={create}>Create token</Button>
      </Stack>
      <Stack spacing={1}>
        {tokens.map(t => (
          <Box key={t.id} sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography sx={{ flexGrow: 1, fontFamily: "'IBM Plex Mono', monospace" }}>{t.name || '(unnamed)'}</Typography>
            <Typography variant="caption" color="text.secondary">{t.prefix}…</Typography>
            {t.revoked_at
              ? <Typography variant="caption" color="text.secondary">revoked</Typography>
              : <Button size="small" color="error" onClick={() => revoke(t.id)}>Revoke</Button>}
          </Box>
        ))}
      </Stack>
    </Paper>
  )
}
