import { Box, Button, Divider, Stack, Typography } from '@mui/material'

const MONO = "'IBM Plex Mono', monospace"

export default function RepoOverview({ home, onOpenFullMap }) {
  return (
    <Box sx={{ maxWidth: 720 }}>
      <Typography variant="h4" sx={{ fontFamily: MONO }}>{home.title}</Typography>
      <Typography color="text.secondary" sx={{ mt: 1.5, fontSize: 16 }}>
        {home.description || 'No description available for this repo.'}
      </Typography>
      <Divider sx={{ my: 3 }} />
      <Stack direction="row" spacing={4}>
        <Box>
          <Typography variant="h5" sx={{ fontFamily: MONO }}>{home.endpoints.length}</Typography>
          <Typography variant="overline" color="text.disabled">endpoints</Typography>
        </Box>
      </Stack>
      <Typography color="text.secondary" sx={{ mt: 3 }}>
        Pick an endpoint on the left to see its decision diagram, fully expanded.
      </Typography>
      <Button
        variant="outlined"
        data-testid="open-full-map"
        onClick={onOpenFullMap}
        sx={{ mt: 3 }}
      >
        Open full repo map
      </Button>
    </Box>
  )
}
