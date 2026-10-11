import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Box, Container, Toolbar } from '@mui/material'
import TopBar from '../components/dashboard/TopBar'
import Sidebar from '../components/dashboard/Sidebar'
import PlaceholderCharts from '../components/dashboard/PlaceholderCharts'
import RepoMapsPanel from '../components/dashboard/RepoMapsPanel'

export default function DashboardPage({ onOpenMap }) {
  const [section, setSection] = useState('repomaps')
  const navigate = useNavigate()
  const routes = { tour: '/tour', brainstorm: '/brainstorm' }
  const select = id => (routes[id] ? navigate(routes[id]) : setSection(id))

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh' }}>
      <TopBar />
      <Sidebar section={section} onSelect={select} />
      <Box component="main" sx={{ flexGrow: 1, minWidth: 0 }}>
        <Toolbar />
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <PlaceholderCharts />
          {section === 'repomaps' && <RepoMapsPanel onOpenMap={onOpenMap} />}
        </Container>
      </Box>
    </Box>
  )
}
