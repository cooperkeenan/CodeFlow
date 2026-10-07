import { Box, Chip, Stack, Typography } from '@mui/material'
import { endpointSlug } from '../../api/flow'

export default function GroupChildCards({ groups, onOpen }) {
  return (
    <Box data-testid="group-children">
      <Typography variant="overline" color="text.disabled">groups ({groups.length})</Typography>
      <Stack spacing={1.5} sx={{ mt: 1 }}>
        {groups.map(child => (
          <Box
            key={child.id}
            data-testid={`group-card-${endpointSlug(child.id)}`}
            onClick={() => onOpen(child.id)}
            sx={{
              cursor: 'pointer',
              p: 2,
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              '&:hover': { borderColor: 'var(--link)' },
            }}
          >
            <Stack direction="row" alignItems="center" spacing={1}>
              <Typography sx={{ fontSize: 15, fontWeight: 500, flexGrow: 1, minWidth: 0 }}>
                {child.name}
              </Typography>
              <Chip label={`${child.route_count} routes`} size="small" variant="outlined" />
            </Stack>
          </Box>
        ))}
      </Stack>
    </Box>
  )
}
