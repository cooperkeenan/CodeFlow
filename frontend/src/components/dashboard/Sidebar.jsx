import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar } from '@mui/material'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import PlayCircleOutlineIcon from '@mui/icons-material/PlayCircleOutline'

const WIDTH = 224

const ITEMS = [
  { id: 'repomaps', label: 'Repo Maps', icon: <AccountTreeIcon fontSize="small" /> },
  { id: 'tour', label: 'Tour', icon: <PlayCircleOutlineIcon fontSize="small" /> },
]

export default function Sidebar({ section, onSelect }) {
  return (
    <Drawer
      variant="permanent"
      sx={{
        width: WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: { width: WIDTH, boxSizing: 'border-box' },
      }}
    >
      <Toolbar />
      <List sx={{ px: 1 }}>
        {ITEMS.map(item => (
          <ListItemButton
            key={item.id}
            selected={section === item.id}
            onClick={() => onSelect(item.id)}
            sx={{ borderRadius: 1, mb: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 36 }}>{item.icon}</ListItemIcon>
            <ListItemText primaryTypographyProps={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 13 }} primary={item.label} />
          </ListItemButton>
        ))}
      </List>
    </Drawer>
  )
}
