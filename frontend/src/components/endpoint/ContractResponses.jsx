import { Box, Chip, Stack, Typography } from '@mui/material'

const MONO = "'IBM Plex Mono', monospace"

export default function ContractResponses({ responses }) {
  if (!responses?.length) return null
  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ fontFamily: MONO, fontSize: 14, mb: 1 }}>Responses</Typography>
      <Stack spacing={1.5}>
        {responses.map(r => (
          <Box key={r.status}>
            <Stack direction="row" alignItems="center" spacing={1}>
              <Chip label={r.status} size="small" color={String(r.status).startsWith('2') ? 'success' : 'default'} />
              <Typography color="text.secondary">{r.description}</Typography>
            </Stack>
            {r.shape && (
              <Box
                component="pre"
                sx={{
                  fontFamily: MONO,
                  fontSize: 11,
                  color: 'text.secondary',
                  bgcolor: 'background.default',
                  border: '1px solid',
                  borderColor: 'divider',
                  borderRadius: 1,
                  p: 1,
                  mt: 0.5,
                  overflowX: 'auto',
                }}
              >
                {typeof r.shape === 'string' ? r.shape : JSON.stringify(r.shape, null, 2)}
              </Box>
            )}
          </Box>
        ))}
      </Stack>
    </Box>
  )
}
