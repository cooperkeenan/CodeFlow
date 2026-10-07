import { useMemo, useState } from 'react'
import { Box, Chip, List, ListItemButton, Stack, Typography } from '@mui/material'
import { endpointSlug } from '../../api/flow'

const INDENT_PX = 16

function ancestorsOf(groups, activeId) {
  const byId = new Map(groups.map(g => [g.id, g]))
  const out = new Set()
  let current = byId.get(activeId)
  while (current?.parent_id) {
    out.add(current.parent_id)
    current = byId.get(current.parent_id)
  }
  return out
}

export default function GroupTree({ groups, activeId, onOpen }) {
  const [toggled, setToggled] = useState(() => new Map())
  const byId = useMemo(() => new Map(groups.map(g => [g.id, g])), [groups])
  const ancestors = useMemo(() => ancestorsOf(groups, activeId), [groups, activeId])
  const isOpen = id => (toggled.has(id) ? toggled.get(id) : ancestors.has(id) || id === activeId)
  const visible = groups.filter(g => {
    let parent = g.parent_id
    while (parent) {
      if (!isOpen(parent)) return false
      parent = byId.get(parent)?.parent_id
    }
    return true
  })

  const onRowClick = group => {
    if (!group.is_leaf) setToggled(prev => new Map(prev).set(group.id, !isOpen(group.id)))
    onOpen(group.id)
  }

  return (
    <Box data-testid="endpoint-list" sx={{ py: 1 }}>
      <List dense disablePadding data-testid="group-tree">
        {visible.map(group => (
          <ListItemButton
            key={group.id}
            data-testid={`endpoint-${endpointSlug(group.id)}`}
            data-active={group.id === activeId ? 'true' : 'false'}
            selected={group.id === activeId}
            onClick={() => onRowClick(group)}
            sx={{
              py: 0.5,
              pl: 2 + group.depth * (INDENT_PX / 8),
              borderLeft: '2px solid transparent',
              '&.Mui-selected': { borderLeftColor: 'var(--area)' },
            }}
          >
            <Stack direction="row" alignItems="center" spacing={1} sx={{ width: '100%', minWidth: 0 }}>
              <Typography sx={{ width: 12, fontSize: 12, color: 'text.disabled', flexShrink: 0 }}>
                {group.is_leaf ? '' : isOpen(group.id) ? '▾' : '▸'}
              </Typography>
              <Typography noWrap sx={{ fontSize: 14, fontWeight: 500, flexGrow: 1, minWidth: 0 }}>
                {group.name}
              </Typography>
              <Chip label={group.route_count} size="small" variant="outlined" />
            </Stack>
          </ListItemButton>
        ))}
      </List>
    </Box>
  )
}
