import { lazy, Suspense, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Box, CircularProgress, Toolbar } from '@mui/material'
import TopBar from '../components/dashboard/TopBar'
import Sidebar from '../components/dashboard/Sidebar'
import RepoPicker from '../components/brainstorm/RepoPicker'
import RepoPathBar from '../components/brainstorm/RepoPathBar'
import { loadPath, savePath } from '../components/brainstorm/brainstormPath'

const BrainstormWorkspace = lazy(() =>
  import('@brainstorm/embed').then(m => ({ default: m.BrainstormWorkspace }))
)
const ROUTES = { repomaps: '/', tour: '/tour' }

function Workspace({ repo, question, onChangeRepo }) {
  const [path, setPath] = useState(() => loadPath(repo))
  const apply = value => { savePath(repo, value); setPath(value) }
  return (
    <>
      <RepoPathBar repo={repo} path={path} onApply={apply} onChangeRepo={onChangeRepo} />
      <Box sx={{ flex: 1, minHeight: 0, position: 'relative' }}>
        <Suspense fallback={<Box sx={{ display: 'grid', placeItems: 'center', height: '100%' }}><CircularProgress /></Box>}>
          <BrainstormWorkspace key={path} repoPath={path} initialQuestion={question} apiBase="/brainstorm-api" />
        </Suspense>
      </Box>
    </>
  )
}

export default function BrainstormPage({ analysis = null }) {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const [picking, setPicking] = useState(false)
  const repo = picking ? null : params.get('repo') || analysis?.repo || null
  const select = id => ROUTES[id] && navigate(ROUTES[id])
  const pick = value => { setPicking(false); setParams({ repo: value }) }

  return (
    <Box sx={{ display: 'flex', height: '100vh' }}>
      <TopBar />
      <Sidebar section="brainstorm" onSelect={select} />
      <Box component="main" sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Toolbar />
        {repo
          ? <Workspace key={repo} repo={repo} question={params.get('q') || undefined} onChangeRepo={() => setPicking(true)} />
          : <RepoPicker onPick={pick} />}
      </Box>
    </Box>
  )
}
