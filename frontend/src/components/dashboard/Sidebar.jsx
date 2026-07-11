import { Drawer, List, ListItemButton, ListItemIcon, ListItemText, Toolbar } from '@mui/material'
import AccountTreeIcon from '@mui/icons-material/AccountTree'
import InsightsIcon from '@mui/icons-material/Insights'
import LayersIcon from '@mui/icons-material/Layers'

const WIDTH = 224

const ITEMS = [
  { id: 'repomaps', label: 'Repo Maps', icon: <AccountTreeIcon fontSize="small" /> },
  { id: 'placeholder1', label: 'Placeholder 1', icon: <InsightsIcon fontSize="small" /> },
  { id: 'placeholder2', label: 'Placeholder 2', icon: <LayersIcon fontSize="small" /> },
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
