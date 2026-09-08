import { Box, Button, Chip, List, ListItemButton, Stack, Typography } from '@mui/material'
import { useQueryClient } from '@tanstack/react-query'
import { endpointSlug } from '../../api/flow'
import { endpointDetailQueryFn, endpointDetailQueryKey } from '../../api/queries'

const MONO = "'IBM Plex Mono', monospace"

function Section({ title, items, onOpen, onHover, activeId }) {
  if (!items.length) return null
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="overline" color="text.disabled" sx={{ px: 2 }}>
        {title} ({items.length})
      </Typography>
      <List dense disablePadding>
        {items.map(item => (
          <ListItemButton
            key={item.id}
            data-testid={`endpoint-${endpointSlug(item.id)}`}
            data-active={item.id === activeId ? 'true' : 'false'}
            selected={item.id === activeId}
            onClick={() => onOpen(item.id)}
            onMouseEnter={() => onHover?.(item.id)}
            onFocus={() => onHover?.(item.id)}
            sx={{ display: 'block', py: 0.75, borderLeft: '2px solid transparent', '&.Mui-selected': { borderLeftColor: 'var(--area)' } }}
          >
            <Stack direction="row" alignItems="center" spacing={1}>
              <Typography
                sx={{ fontSize: 14, fontWeight: 500, color: 'text.primary', flexGrow: 1, minWidth: 0, '.MuiListItemButton-root:hover &': { color: 'var(--link)' } }}
              >
                {item.title}
              </Typography>
              {item.route_count > 1 && (
                <Chip label={item.route_count} size="small" variant="outlined" />
              )}
            </Stack>
            <Typography
              variant="caption"
              color="text.secondary"
              noWrap
              component="div"
              sx={{ fontFamily: MONO }}
            >
              {item.label}
            </Typography>
          </ListItemButton>
        ))}
      </List>
    </Box>
  )
}

export default function EndpointList({ endpoints, onOpen, repo, canPrefetch = true, activeId = null, onOverview = null }) {
  const queryClient = useQueryClient()
  const prefetch = (entryId) => {
    if (!canPrefetch || !repo) return
    queryClient.prefetchQuery({
      queryKey: endpointDetailQueryKey(repo, null, entryId),
      queryFn: endpointDetailQueryFn(repo, null, entryId),
    })
  }

  return (
    <Box data-testid="endpoint-list" sx={{ py: 2 }}>
      {onOverview && (
        <Box sx={{ px: 2, pb: 1.5 }}>
          <Button
            fullWidth
            size="small"
            variant="contained"
            data-testid="repo-overview"
            onClick={onOverview}
            sx={{ fontFamily: MONO, fontSize: 12, justifyContent: 'flex-start' }}
          >
            overview
          </Button>
        </Box>
      )}
      <Section title="Endpoints" items={endpoints} onOpen={onOpen} onHover={prefetch} activeId={activeId} />
      {!endpoints.length && (
        <Typography color="text.secondary" sx={{ px: 2 }}>
          No HTTP endpoints detected in this repo.
        </Typography>
      )}
    </Box>
  )
}
