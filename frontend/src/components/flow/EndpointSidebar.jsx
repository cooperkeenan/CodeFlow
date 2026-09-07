import { Box, List, ListItemButton, Stack, Typography } from '@mui/material'
import { useNavigate } from 'react-router-dom'
import { endpointSlug } from '../../api/flow'
import { useRepoHome } from '../../hooks/useRepoHome'

const MONO = "'IBM Plex Mono', monospace"
const REPO_HOME_FIXTURE = '/fixture/repo_home.json'

function Row({ item, active, onOpen, onOverview }) {
  return (
    <ListItemButton
      data-testid={`sidebar-endpoint-${endpointSlug(item.id)}`}
      data-active={active ? 'true' : 'false'}
      selected={active}
      onClick={() => onOpen(item.id)}
      sx={{ display: 'flex', alignItems: 'center', gap: 1, py: 0.75, px: 1.5 }}
    >
      <Typography
        sx={{
          fontFamily: MONO,
          fontSize: 13,
          color: active ? 'primary.light' : 'primary.main',
          flexGrow: 1,
          minWidth: 0,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
      >
        {item.label}
      </Typography>
      <Typography
        component="span"
        data-testid={`sidebar-overview-${endpointSlug(item.id)}`}
        onClick={e => { e.stopPropagation(); onOverview(item.id) }}
        sx={{
          fontFamily: MONO,
          fontSize: 12,
          color: 'text.secondary',
          flexShrink: 0,
          '&:hover': { color: 'primary.main', textDecoration: 'underline' },
        }}
      >
        overview
      </Typography>
    </ListItemButton>
  )
}

function Section({ title, items, entry, onOpen, onOverview }) {
  if (!items.length) return null
  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="overline" color="text.disabled" sx={{ px: 1.5 }}>
        {title} ({items.length})
      </Typography>
      <List dense disablePadding>
        {items.map(item => (
          <Row key={item.id} item={item} active={item.id === entry} onOpen={onOpen} onOverview={onOverview} />
        ))}
      </List>
    </Box>
  )
}

export default function EndpointSidebar({ repo, fixture, entry, flowPath, endpointPath = '/endpoint' }) {
  const navigate = useNavigate()
  const { home, loading } = useRepoHome(repo, fixture ? REPO_HOME_FIXTURE : null)

  const endpoints = home?.endpoints ?? []
  const entryPoints = home?.entry_points ?? []

  if (loading || !home || (!endpoints.length && !entryPoints.length)) return null

  const onOpen = id => navigate(`${flowPath}?entry=${encodeURIComponent(id)}`)
  const onOverview = id => navigate(`${endpointPath}?entry=${encodeURIComponent(id)}`)

  return (
    <Stack
      data-testid="endpoint-sidebar"
      sx={{
        width: 240,
        flexShrink: 0,
        height: '100%',
        overflowY: 'auto',
        borderRight: '1px solid',
        borderColor: 'divider',
        py: 1.5,
      }}
    >
      <Section title="Endpoints" items={endpoints} entry={entry} onOpen={onOpen} onOverview={onOverview} />
      <Section title="Entry points" items={entryPoints} entry={entry} onOpen={onOpen} onOverview={onOverview} />
    </Stack>
  )
}
