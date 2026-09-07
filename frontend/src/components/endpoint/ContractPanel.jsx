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

export default function ContractPanel({ contracts, title }) {
  const routes = (contracts || []).filter(Boolean)
  if (!routes.length) return null
  return (
    <Box data-testid="contract-panel" sx={{ maxWidth: 720 }}>
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
        {routes.map(contract => (
          <ContractRoute key={`${contract.method}:${contract.path}`} contract={contract} />
        ))}
      </Stack>
    </Box>
  )
}
