import { Box, Chip, List, ListItemButton, Stack, Typography } from '@mui/material'
import { useQueryClient } from '@tanstack/react-query'
import { endpointSlug } from '../../api/flow'
import { flowQueryFn, flowQueryKey } from '../../api/queries'

const MONO = "'IBM Plex Mono', monospace"

function Section({ title, items, onOpen, onHover }) {
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
            onClick={() => onOpen(item.id)}
            onMouseEnter={() => onHover?.(item.id)}
            onFocus={() => onHover?.(item.id)}
            sx={{ display: 'block', py: 0.75 }}
          >
            <Stack direction="row" alignItems="center" spacing={1}>
              <Typography
                sx={{ fontFamily: MONO, fontSize: 13, color: 'primary.main', flexGrow: 1 }}
              >
                {item.label}
              </Typography>
              {item.route_count > 1 && (
                <Chip label={item.route_count} size="small" variant="outlined" />
              )}
            </Stack>
            <Typography variant="caption" color="text.secondary" noWrap component="div">
              {item.title}
            </Typography>
          </ListItemButton>
        ))}
      </List>
    </Box>
  )
}

export default function EndpointList({ endpoints, onOpen, repo, canPrefetch = true }) {
  const queryClient = useQueryClient()
  const prefetch = (entryId) => {
    if (!canPrefetch || !repo) return
    queryClient.prefetchQuery({
      queryKey: flowQueryKey(repo, null, entryId, null),
      queryFn: flowQueryFn(repo, null, entryId, null),
    })
  }

  return (
    <Box data-testid="endpoint-list" sx={{ py: 2 }}>
      <Section title="Endpoints" items={endpoints} onOpen={onOpen} onHover={prefetch} />
      {!endpoints.length && (
        <Typography color="text.secondary" sx={{ px: 2 }}>
          No HTTP endpoints detected in this repo.
        </Typography>
      )}
    </Box>
  )
}
