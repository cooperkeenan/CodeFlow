import { Box, Paper, Typography } from '@mui/material'
import { LineChart } from '@mui/x-charts/LineChart'
import { BarChart } from '@mui/x-charts/BarChart'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
const ACCENT = '#39FF14'
const BLUE = '#64B5F6'

function ChartCard({ title, children }) {
  return (
    <Paper sx={{ p: 2, flex: '1 1 320px', minWidth: 0 }}>
      <Typography variant="overline" color="text.secondary">{title}</Typography>
      <Box sx={{ height: 220 }}>{children}</Box>
    </Paper>
  )
}

export default function PlaceholderCharts() {
  return (
    <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', mb: 3 }}>
      <ChartCard title="Analyses over time (sample)">
        <LineChart
          xAxis={[{ scaleType: 'point', data: MONTHS }]}
          series={[{ data: [4, 6, 5, 9, 8, 12], color: ACCENT, area: true }]}
          height={220}
        />
      </ChartCard>
      <ChartCard title="Modules per repo (sample)">
        <BarChart
          xAxis={[{ scaleType: 'band', data: ['repo-a', 'repo-b', 'repo-c', 'repo-d'] }]}
          series={[{ data: [8, 14, 5, 11], color: BLUE }]}
          height={220}
        />
      </ChartCard>
    </Box>
  )
}
