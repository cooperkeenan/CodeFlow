import { useEffect, useState } from 'react'
import { Box, Button, InputBase, Typography } from '@mui/material'

const MONO = "'IBM Plex Mono', monospace"

export default function RepoPathBar({ repo, path, onApply, onChangeRepo }) {
  const [draft, setDraft] = useState(path)
  useEffect(() => setDraft(path), [path])
  const apply = () => {
    const next = draft.trim()
    if (next) onApply(next)
  }
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, px: 2, py: 0.75, borderBottom: '1px solid', borderColor: 'divider' }}>
      <Typography sx={{ fontFamily: MONO, fontSize: 12, color: 'text.secondary' }}>{repo}</Typography>
      <InputBase
        value={draft}
        onChange={e => setDraft(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && apply()}
        onBlur={() => setDraft(path)}
        inputProps={{ 'aria-label': 'local repo path', spellCheck: false }}
        sx={{ flex: 1, fontFamily: MONO, fontSize: 12, px: 1, border: '1px solid', borderColor: 'divider', borderRadius: 0.5 }}
      />
      <Button size="small" onClick={onChangeRepo} sx={{ fontFamily: MONO, fontSize: 11 }}>change repo</Button>
    </Box>
  )
}
