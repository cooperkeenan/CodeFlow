import { Box, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'

const MONO = "'IBM Plex Mono', monospace"

function ParamGroup({ location, params }) {
  return (
    <Box sx={{ mb: 1.5 }}>
      <Typography variant="caption" color="text.disabled" component="div">{location}</Typography>
      <Table size="small" sx={{ tableLayout: 'fixed', width: '100%' }}>
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: '24%' }}>name</TableCell>
            <TableCell sx={{ width: '16%' }}>type</TableCell>
            <TableCell sx={{ width: '12%' }}>required</TableCell>
            <TableCell>description</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {params.map(p => (
            <TableRow key={p.name}>
              <TableCell sx={{ fontFamily: MONO, fontSize: 12, overflowWrap: 'anywhere' }}>
                {p.name}
              </TableCell>
              <TableCell sx={{ fontFamily: MONO, fontSize: 12, overflowWrap: 'anywhere' }}>
                {p.type}
              </TableCell>
              <TableCell>{p.required ? 'yes' : 'no'}</TableCell>
              <TableCell sx={{ color: 'text.secondary' }}>{p.description}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Box>
  )
}

export default function ContractParamTable({ params }) {
  if (!params?.length) return null
  const byLocation = params.reduce((acc, p) => {
    (acc[p.location] ??= []).push(p)
    return acc
  }, {})
  return (
    <Box>
      {Object.entries(byLocation).map(([location, items]) => (
        <ParamGroup key={location} location={location} params={items} />
      ))}
    </Box>
  )
}
