import { Alert, AlertTitle, Button } from '@mui/material'
import GitHubIcon from '@mui/icons-material/GitHub'
import { startGithubOAuth } from '../../api/github'

export default function GithubLinkPrompt({ title, children }) {
  return (
    <Alert
      severity="info"
      sx={{ mb: 2 }}
      action={
        <Button
          color="inherit"
          size="small"
          variant="outlined"
          startIcon={<GitHubIcon />}
          onClick={startGithubOAuth}
        >
          Link GitHub
        </Button>
      }
    >
      <AlertTitle>{title}</AlertTitle>
      {children}
    </Alert>
  )
}
