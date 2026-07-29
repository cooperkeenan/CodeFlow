import { createContext, useContext, useEffect, useState } from 'react'
import { listRepoMaps } from '../api/repomaps'

const RepoMapsContext = createContext(null)

export function RepoMapsProvider({ children }) {
  const [maps, setMaps] = useState([])
  const [error, setError] = useState(null)

  const refresh = () =>
    listRepoMaps()
      .then(d => setMaps(d.repo_maps))
      .catch(e => setError(e.message))

  useEffect(() => { refresh() }, [])

  return (
    <RepoMapsContext.Provider value={{ maps, error, refresh }}>
      {children}
    </RepoMapsContext.Provider>
  )
}

export function useRepoMaps() {
  return useContext(RepoMapsContext)
}
