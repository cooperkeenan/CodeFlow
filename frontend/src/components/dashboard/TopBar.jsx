import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AppBar, Avatar, Box, IconButton, Menu, MenuItem, Toolbar, Typography, Divider, ListItemIcon } from '@mui/material'
import GitHubIcon from '@mui/icons-material/GitHub'
import SettingsIcon from '@mui/icons-material/Settings'
import LogoutIcon from '@mui/icons-material/Logout'
import { clearSession, getUser } from '../../api/session'
import { startGithubOAuth } from '../../api/github'

export default function TopBar() {
  const navigate = useNavigate()
  const user = getUser()
  const [anchor, setAnchor] = useState(null)
  const close = () => setAnchor(null)

  const logout = () => { clearSession(); navigate('/login') }
  const label = user?.github_login || user?.email || '?'

  return (
    <AppBar position="fixed" color="default" elevation={0} sx={{ zIndex: theme => theme.zIndex.drawer + 1, borderBottom: '1px solid', borderColor: 'divider' }}>
      <Toolbar sx={{ gap: 1 }}>
        <Typography component="span" sx={{ fontFamily: "'IBM Plex Mono', monospace", color: 'primary.main', fontWeight: 700 }}>//</Typography>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>CodeFlow</Typography>
        <IconButton onClick={e => setAnchor(e.currentTarget)} size="small">
          <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main', color: 'primary.contrastText', fontSize: 14 }}>
            {label[0]?.toUpperCase()}
          </Avatar>
        </IconButton>
        <Menu anchorEl={anchor} open={Boolean(anchor)} onClose={close}>
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="body2" color="text.secondary">Signed in as</Typography>
            <Typography variant="body2">{label}</Typography>
          </Box>
          <Divider />
          <MenuItem onClick={() => { close(); startGithubOAuth() }}>
            <ListItemIcon><GitHubIcon fontSize="small" /></ListItemIcon>
            {user?.github_login ? 'Re-link GitHub' : 'Link GitHub'}
          </MenuItem>
          <MenuItem onClick={() => { close(); navigate('/settings') }}>
            <ListItemIcon><SettingsIcon fontSize="small" /></ListItemIcon>
            Settings
          </MenuItem>
          <MenuItem onClick={() => { close(); logout() }}>
            <ListItemIcon><LogoutIcon fontSize="small" /></ListItemIcon>
            Log out
          </MenuItem>
        </Menu>
      </Toolbar>
    </AppBar>
  )
}
