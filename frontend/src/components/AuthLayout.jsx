import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export default function AuthLayout({ title, subtitle, children }) {
  return (
    <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center', p: 2 }}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 380 }}>
        <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 0.75, mb: 0.5 }}>
          <Typography component="span" sx={{ fontFamily: "'IBM Plex Mono', monospace", color: 'primary.main', fontWeight: 700 }}>//</Typography>
          <Typography component="span" variant="h6">CodeFlow</Typography>
        </Box>
        <Typography variant="h5" sx={{ mt: 2 }}>{title}</Typography>
        {subtitle && <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{subtitle}</Typography>}
        <Box sx={{ mt: 3 }}>{children}</Box>
      </Paper>
    </Box>
  )
}
