import { createContext, useContext, useEffect, useState } from 'react'
import { listRepoMaps } from '../api/repomaps'

const RepoMapsContext = createContext(null)

export function RepoMapsProvider({ children }) {
  const [maps, setMaps] = useState([])
  const [error, setError] = useState(null)
  const [signedOut, setSignedOut] = useState(false)

  const refresh = () =>
    listRepoMaps()
      .then(d => { setMaps(d.repo_maps); setError(null); setSignedOut(false) })
      .catch(e => (e.status === 401 ? setSignedOut(true) : setError(e.message)))

  useEffect(() => { refresh() }, [])

  return (
    <RepoMapsContext.Provider value={{ maps, error, signedOut, refresh }}>
      {children}
    </RepoMapsContext.Provider>
  )
}

export function useRepoMaps() {
  return useContext(RepoMapsContext)
}
