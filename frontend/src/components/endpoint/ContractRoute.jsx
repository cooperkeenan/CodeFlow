import { Box, Chip, Paper, Stack, Typography } from '@mui/material'
import CodeBlock from './CodeBlock'
import ContractErrorCodes from './ContractErrorCodes'
import ContractParamTable from './ContractParamTable'
import ContractSection from './ContractSection'
import { methodChipSx, statusChipSx } from './contractChips'

const MONO = "'IBM Plex Mono', monospace"

const isSuccess = status => /^[23]/.test(String(status))

export default function ContractRoute({ contract }) {
  if (!contract) return null
  const name = contract.name || contract.summary
  const description = contract.name ? contract.summary : ''
  const responses = contract.responses || []
  const success = responses.find(r => isSuccess(r.status))
  const errors = responses.filter(r => !isSuccess(r.status))
  const responseBody = contract.example_response || success?.shape || ''
  const requestBody = contract.example_request || contract.request_body

  return (
    <Paper
      variant="outlined"
      data-testid="contract-route"
      sx={{ bgcolor: 'background.paper', borderColor: 'divider', borderRadius: 1, p: 2.5 }}
    >
      {name && <Typography sx={{ fontWeight: 700, fontSize: 15 }}>{name}</Typography>}
      {description && (
        <Typography color="text.secondary" sx={{ mt: 0.5 }}>{description}</Typography>
      )}

      <ContractSection title="Request URL">
        <Box>
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip
              label={contract.method || '?'}
              size="small"
              variant="outlined"
              sx={methodChipSx(contract.method)}
            />
            <Typography sx={{ fontFamily: MONO, fontSize: 13, overflowWrap: 'anywhere' }}>
              {contract.path || '/'}
            </Typography>
          </Stack>
          {contract.auth && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Auth:</strong> {contract.auth}
            </Typography>
          )}
        </Box>
      </ContractSection>

      <ContractSection title="Params / Headers">
        {contract.params?.length ? (
          <ContractParamTable params={contract.params} />
        ) : (
          <Typography variant="body2" color="text.disabled">none</Typography>
        )}
      </ContractSection>

      <ContractSection title="Example request">
        {requestBody ? (
          <CodeBlock value={requestBody} />
        ) : (
          <Typography variant="body2" color="text.disabled">none</Typography>
        )}
      </ContractSection>

      <ContractSection title="Example response">
        <Box>
          {success && (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 0.75 }}>
              <Chip
                label={success.status}
                size="small"
                variant="outlined"
                sx={statusChipSx(success.status)}
              />
              <Typography variant="body2" color="text.secondary">
                {success.description}
              </Typography>
            </Stack>
          )}
          {responseBody ? (
            <CodeBlock value={responseBody} />
          ) : (
            <Typography variant="body2" color="text.disabled">none</Typography>
          )}
        </Box>
      </ContractSection>

      <ContractErrorCodes responses={errors} />
    </Paper>
  )
}
