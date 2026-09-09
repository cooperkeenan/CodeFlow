import { useState } from 'react'
import { Box, Button, Stack, Typography } from '@mui/material'
import ContractRoute from './ContractRoute'
import { contractsToOpenApiText } from '../../lib/contractToOpenApi'

const MONO = "'IBM Plex Mono', monospace"

function CopyOpenApiButton({ contracts, title }) {
  const [state, setState] = useState('copy OpenAPI')
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(contractsToOpenApiText(contracts, { title }))
      setState('copied')
    } catch {
      setState('copy failed')
    }
    setTimeout(() => setState('copy OpenAPI'), 2000)
  }
  return (
    <Button
      size="small"
      variant="outlined"
      color="inherit"
      data-testid="copy-openapi"
      onClick={copy}
      sx={{ fontSize: 11, color: 'text.secondary', borderColor: 'divider' }}
    >
      {state}
    </Button>
  )
}

export default function ContractPanel({ contracts, title, selectedKey = null, onSelect = null }) {
  const routes = (contracts || []).filter(Boolean)
  if (!routes.length) return null
  return (
    <Box data-testid="contract-panel" sx={{ maxWidth: '100%' }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1.5 }}>
        <Typography variant="h6" sx={{ fontFamily: MONO, fontSize: 16 }}>API Contract</Typography>
        {routes.length > 1 && (
          <Typography variant="caption" color="text.disabled">
            {routes.length} routes
          </Typography>
        )}
        <Box sx={{ flex: 1 }} />
        <CopyOpenApiButton contracts={routes} title={title} />
      </Stack>
      <Stack spacing={2}>
        {routes.map(contract => {
          const key = `${contract.method}:${contract.path}`
          return (
            <Box
              key={key}
              data-testid={`contract-card-${key}`}
              data-selected={key === selectedKey ? 'true' : 'false'}
              onClick={() => onSelect?.(key === selectedKey ? null : key)}
              sx={{
                cursor: onSelect ? 'pointer' : 'default',
                borderRadius: 1,
                outline: key === selectedKey ? '1px solid #C6F135' : '1px solid transparent',
                boxShadow: key === selectedKey ? '0 0 18px -4px rgba(198,241,53,0.45)' : 'none',
                transition: 'outline-color 160ms ease, box-shadow 160ms ease',
              }}
            >
              <ContractRoute contract={contract} />
            </Box>
          )
        })}
      </Stack>
    </Box>
  )
}
