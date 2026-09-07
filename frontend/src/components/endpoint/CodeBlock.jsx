import { Box } from '@mui/material'

const MONO = "'IBM Plex Mono', monospace"

function pretty(value) {
  if (value == null) return ''
  if (typeof value !== 'string') return JSON.stringify(value, null, 2)
  const trimmed = value.trim()
  if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) return value
  try {
    return JSON.stringify(JSON.parse(trimmed), null, 2)
  } catch {
    return value
  }
}

export default function CodeBlock({ value }) {
  if (!value) return null
  return (
    <Box>
      <Box
        component="pre"
        sx={{
          fontFamily: MONO,
          fontSize: 11.5,
          lineHeight: 1.65,
          color: 'text.secondary',
          bgcolor: 'background.default',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          p: 1.25,
          m: 0,
          whiteSpace: 'pre-wrap',
          overflowWrap: 'anywhere',
        }}
      >
        {pretty(value)}
      </Box>
    </Box>
  )
}
