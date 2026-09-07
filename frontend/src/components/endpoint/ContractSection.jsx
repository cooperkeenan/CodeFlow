import { Box, Typography } from '@mui/material'

export default function ContractSection({ title, children, dense = false }) {
  if (!children) return null
  return (
    <Box sx={{ mt: dense ? 1.5 : 2 }}>
      <Typography
        variant="overline"
        color="text.disabled"
        component="div"
        sx={{ display: 'block', mb: 0.75 }}
      >
        {title}
      </Typography>
      {children}
    </Box>
  )
}
