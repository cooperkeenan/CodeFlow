import { Box } from '@mui/material'
import EndpointList from '../repo/EndpointList'
import GroupTree from './GroupTree'

export default function EndpointRail({ endpoints, groups, open, onOpen, onOverview, repo, canPrefetch, activeId }) {
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
      {groups?.length ? (
        <GroupTree groups={groups} activeId={activeId} onOpen={onOpen} />
      ) : (
        <EndpointList
          endpoints={endpoints}
          onOpen={onOpen}
          repo={repo}
          canPrefetch={canPrefetch}
          activeId={activeId}
          onOverview={onOverview}
        />
      )}
    </Box>
  )
}
