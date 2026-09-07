import { useState } from 'react'
import {
  Box, Button, Chip, Table, TableBody, TableCell, TableHead, TableRow, Typography,
} from '@mui/material'
import { statusChipSx } from './contractChips'

export default function ContractErrorCodes({ responses }) {
  const [open, setOpen] = useState(false)
  if (!responses?.length) return null
  return (
    <Box sx={{ mt: 2 }}>
      <Button
        size="small"
        variant="text"
        color="inherit"
        data-testid="error-codes-toggle"
        onClick={() => setOpen(value => !value)}
        sx={{ fontSize: 11, color: 'text.secondary', px: 0.5 }}
      >
        {open ? '▾' : '▸'} error codes ({responses.length})
      </Button>
      {open && (
        <Table
          size="small"
          data-testid="error-codes-table"
          sx={{ tableLayout: 'fixed', width: '100%', mt: 0.5 }}
        >
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: '18%' }}>status</TableCell>
              <TableCell>description</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {responses.map(r => (
              <TableRow key={r.status}>
                <TableCell>
                  <Chip label={r.status} size="small" variant="outlined" sx={statusChipSx(r.status)} />
                </TableCell>
                <TableCell sx={{ color: 'text.secondary' }}>
                  <Typography variant="body2">{r.description}</Typography>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </Box>
  )
}
