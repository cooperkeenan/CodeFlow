import { useState } from 'react'
import { Box, Container, Toolbar } from '@mui/material'
import TopBar from '../components/dashboard/TopBar'
import Sidebar from '../components/dashboard/Sidebar'
import PlaceholderCharts from '../components/dashboard/PlaceholderCharts'
import RepoMapsPanel from '../components/dashboard/RepoMapsPanel'
import PlaceholderPanel from '../components/dashboard/PlaceholderPanel'

export default function DashboardPage({ onOpenMap }) {
  const [section, setSection] = useState('repomaps')

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar />
      <Sidebar section={section} onSelect={setSection} />
      <Box component="main" sx={{ flexGrow: 1, minWidth: 0 }}>
        <Toolbar />
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <PlaceholderCharts />
          {section === 'repomaps' && <RepoMapsPanel onOpenMap={onOpenMap} />}
          {section === 'placeholder1' && <PlaceholderPanel title="Placeholder 1" />}
          {section === 'placeholder2' && <PlaceholderPanel title="Placeholder 2" />}
        </Container>
      </Box>
    </Box>
  )
}
