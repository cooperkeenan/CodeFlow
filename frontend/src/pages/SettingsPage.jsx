import { Box, Button, Chip, Container, Paper, Stack, Toolbar, Typography } from '@mui/material'
import GitHubIcon from '@mui/icons-material/GitHub'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { useNavigate } from 'react-router-dom'
import TopBar from '../components/dashboard/TopBar'
import TokenManager from '../components/settings/TokenManager'
import { startGithubOAuth } from '../api/github'
import { getUser } from '../api/session'

export default function SettingsPage() {
  const navigate = useNavigate()
  const user = getUser()
  const linked = Boolean(user?.github_login)

  return (
    <Box sx={{ minHeight: '100vh' }}>
      <TopBar />
      <Toolbar />
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/')} sx={{ mb: 2 }}>Back</Button>
        <Typography variant="h5" gutterBottom>Settings</Typography>

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>GitHub</Typography>
          <Stack direction="row" alignItems="center" spacing={2}>
            {linked
              ? <Chip color="success" variant="outlined" label={`Linked as ${user.github_login}`} />
              : <Typography variant="body2" color="text.secondary">Link GitHub to import repositories when off-firewall.</Typography>}
            <Box sx={{ flexGrow: 1 }} />
            <Button variant="outlined" color="secondary" startIcon={<GitHubIcon />} onClick={startGithubOAuth}>
              {linked ? 'Re-link GitHub' : 'Link GitHub'}
            </Button>
          </Stack>
        </Paper>

        <TokenManager />
      </Container>
    </Box>
  )
}
