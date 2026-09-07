import { Box, Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material'

const MONO = "'IBM Plex Mono', monospace"

function ParamGroup({ location, params }) {
  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="overline" color="text.disabled">{location}</Typography>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>name</TableCell>
            <TableCell>type</TableCell>
            <TableCell>required</TableCell>
            <TableCell>description</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {params.map(p => (
            <TableRow key={p.name}>
              <TableCell sx={{ fontFamily: MONO, fontSize: 12 }}>{p.name}</TableCell>
              <TableCell sx={{ fontFamily: MONO, fontSize: 12 }}>{p.type}</TableCell>
              <TableCell>{p.required ? 'yes' : 'no'}</TableCell>
              <TableCell color="text.secondary">{p.description}</TableCell>
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
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ fontFamily: MONO, fontSize: 14, mb: 1 }}>Parameters</Typography>
      {Object.entries(byLocation).map(([location, items]) => (
        <ParamGroup key={location} location={location} params={items} />
      ))}
    </Box>
  )
}
