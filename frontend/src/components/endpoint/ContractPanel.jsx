import { Box, Chip, Divider, Stack, Typography } from '@mui/material'
import ContractParamTable from './ContractParamTable'
import ContractResponses from './ContractResponses'

const MONO = "'IBM Plex Mono', monospace"

function Example({ title, value }) {
  if (!value) return null
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="overline" color="text.disabled">{title}</Typography>
      <Box
        component="pre"
        sx={{
          fontFamily: MONO,
          fontSize: 11,
          color: 'text.secondary',
          bgcolor: 'background.default',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1,
          p: 1,
          overflowX: 'auto',
        }}
      >
        {typeof value === 'string' ? value : JSON.stringify(value, null, 2)}
      </Box>
    </Box>
  )
}

export default function ContractPanel({ contract }) {
  if (!contract) return null
  return (
    <Box data-testid="contract-panel" sx={{ maxWidth: 720 }}>
      <Stack direction="row" alignItems="center" spacing={1.5} sx={{ mb: 1 }}>
        <Typography variant="h6" sx={{ fontFamily: MONO, fontSize: 16 }}>API Contract</Typography>
        {contract.generated === false && (
          <Typography variant="caption" color="text.disabled">
            derived statically, not model-generated
          </Typography>
        )}
      </Stack>
      <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1.5 }}>
        <Chip label={contract.method} size="small" color="primary" />
        <Typography sx={{ fontFamily: MONO, fontSize: 13 }}>{contract.path}</Typography>
      </Stack>
      {contract.summary && (
        <Typography color="text.secondary" sx={{ mb: 2 }}>{contract.summary}</Typography>
      )}
      {contract.auth && (
        <Typography variant="body2" sx={{ mb: 2 }}>
          <strong>Auth:</strong> {contract.auth}
        </Typography>
      )}
      <ContractParamTable params={contract.params} />
      {contract.request_body && (
        <Example title="Request body" value={contract.request_body} />
      )}
      <ContractResponses responses={contract.responses} />
      {(contract.example_request || contract.example_response) && <Divider sx={{ my: 2 }} />}
      <Example title="Example request" value={contract.example_request} />
      <Example title="Example response" value={contract.example_response} />
    </Box>
  )
}
