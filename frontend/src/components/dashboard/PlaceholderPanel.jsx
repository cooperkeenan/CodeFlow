import { Box, Paper, Typography } from '@mui/material'
import ConstructionIcon from '@mui/icons-material/Construction'

export default function PlaceholderPanel({ title }) {
  return (
    <Paper sx={{ p: 6 }}>
      <Box sx={{ display: 'grid', placeItems: 'center', gap: 1, color: 'text.secondary' }}>
        <ConstructionIcon fontSize="large" />
        <Typography variant="h6">{title}</Typography>
        <Typography variant="body2">Coming soon.</Typography>
      </Box>
    </Paper>
  )
}
