import { useEffect, useState } from 'react'
import {
  Alert,
  CircularProgress,
  Dialog,
  DialogContent,
  DialogTitle,
  InputAdornment,
  List,
  ListItemButton,
  ListItemText,
  TextField,
} from '@mui/material'
import SearchIcon from '@mui/icons-material/Search'
import { listMyRepos } from '../../api/github'

export default function GithubRepoPicker({ open, onClose, onSelect }) {
  const [repos, setRepos] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    if (!open) return
    setError(null)
    setQuery('')
    setLoading(true)
    listMyRepos()
      .then(d => setRepos(d.repositories.filter(r => r.language === 'Python')))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [open])

  const filtered = repos.filter(r =>
    r.full_name.toLowerCase().includes(query.toLowerCase())
  )

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="sm">
      <DialogTitle>Select a GitHub Repo</DialogTitle>
      <DialogContent>
        <TextField
          fullWidth
          size="small"
          placeholder="Search…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          sx={{ mb: 2 }}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon fontSize="small" />
              </InputAdornment>
            ),
          }}
        />
        {loading && <CircularProgress size={24} />}
        {error && <Alert severity="error">{error}</Alert>}
        {!loading && !error && (
          <List dense disablePadding>
            {filtered.map(r => (
              <ListItemButton key={r.full_name} onClick={() => onSelect(r.full_name)}>
                <ListItemText primary={r.full_name} secondary={r.description || undefined} />
              </ListItemButton>
            ))}
          </List>
        )}
      </DialogContent>
    </Dialog>
  )
}
