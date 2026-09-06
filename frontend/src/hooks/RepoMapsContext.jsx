import { createContext, useContext } from 'react'
import { useQuery } from '@tanstack/react-query'
import { repoMapListQueryFn, repoMapListQueryKey } from '../api/queries'

const RepoMapsContext = createContext(null)

export function RepoMapsProvider({ children }) {
  const { data, error, refetch } = useQuery({
    queryKey: repoMapListQueryKey(),
    queryFn: repoMapListQueryFn(),
  })

  const signedOut = error?.status === 401
  const errorMessage = !signedOut && error ? error.message : null

  return (
    <RepoMapsContext.Provider
      value={{ maps: data?.repo_maps ?? [], error: errorMessage, signedOut, refresh: refetch }}
    >
      {children}
    </RepoMapsContext.Provider>
  )
}

export function useRepoMaps() {
  return useContext(RepoMapsContext)
}
