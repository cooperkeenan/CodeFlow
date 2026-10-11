import { Box, Typography } from '@mui/material'

export function BrainstormWorkspace() {
  return (
    <Box sx={{ p: 3 }}>
      <Typography sx={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 13, color: 'text.disabled' }}>
        Brainstorm isn't available in this build
      </Typography>
    </Box>
  )
}

export default BrainstormWorkspace
