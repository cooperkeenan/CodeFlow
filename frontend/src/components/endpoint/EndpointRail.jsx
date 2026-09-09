import { Box } from '@mui/material'
import EndpointList from '../repo/EndpointList'

export default function EndpointRail({ endpoints, open, onOpen, onOverview, repo, canPrefetch, activeId }) {
  if (!open || !endpoints?.length) return null
  return (
    <Box
      data-testid="endpoint-rail"
      sx={{
        width: 320,
        flexShrink: 0,
        overflowY: 'auto',
        borderRight: '1px solid',
        borderColor: 'divider',
      }}
    >
      <EndpointList
        endpoints={endpoints}
        onOpen={onOpen}
        repo={repo}
        canPrefetch={canPrefetch}
        activeId={activeId}
        onOverview={onOverview}
      />
    </Box>
  )
}
