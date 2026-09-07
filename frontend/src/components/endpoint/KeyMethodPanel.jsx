import { useState } from 'react'
import { Box, List, ListItemButton, Stack, Typography } from '@mui/material'
import CodeView from '../flow/isolate/CodeView'

const MONO = "'IBM Plex Mono', monospace"

const testIdFor = (fqn) => `key-method-${fqn.replace(/[^A-Za-z0-9]+/g, '_')}`

function MethodList({ methods, sources, onSelect }) {
  return (
    <List dense disablePadding>
      {methods.map(m => (
        <ListItemButton
          key={m.fqn}
          data-testid={testIdFor(m.fqn)}
          onClick={() => onSelect(m)}
          sx={{ display: 'block', py: 0.75, borderBottom: '1px solid', borderColor: 'divider' }}
        >
          <Stack direction="row" alignItems="center" spacing={1}>
            <Typography sx={{ fontFamily: MONO, fontSize: 13, color: 'primary.main', flexGrow: 1 }}>
              {m.name}
            </Typography>
            <Typography variant="caption" color="text.disabled" sx={{ fontFamily: MONO }}>
              {m.file}:{m.line}
            </Typography>
          </Stack>
          {m.summary && (
            <Typography variant="caption" color="text.secondary" component="div">
              {m.summary}
            </Typography>
          )}
        </ListItemButton>
      ))}
    </List>
  )
}

export default function KeyMethodPanel({ methods, sources }) {
  const [selected, setSelected] = useState(null)

  if (!methods?.length) return null

  if (selected) {
    const source = sources?.[selected.fqn]
    return (
      <Box sx={{ maxWidth: 720 }}>
        <button className="back" data-testid="method-back" onClick={() => setSelected(null)}>
          ← back to methods
        </button>
        <Box sx={{ mt: 1.5, height: 420 }} data-testid="method-code">
          {source
            ? <CodeView fqn={selected.fqn} name={selected.name} source={source} />
            : (
              <Typography color="text.disabled" sx={{ fontFamily: MONO, fontSize: 12, p: 1 }}>
                no source available for {selected.fqn}
              </Typography>
            )}
        </Box>
      </Box>
    )
  }

  return (
    <Box sx={{ maxWidth: 720 }}>
      <Typography variant="h6" sx={{ fontFamily: MONO, fontSize: 16, mb: 1 }}>Key Methods</Typography>
      <MethodList methods={methods} sources={sources} onSelect={setSelected} />
    </Box>
  )
}
