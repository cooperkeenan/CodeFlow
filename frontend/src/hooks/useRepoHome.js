import { useQuery } from '@tanstack/react-query'
import { repoHomeQueryFn, repoHomeQueryKey } from '../api/queries'

export function useRepoHome(repo, fixtureUrl) {
  const { data, isLoading, error } = useQuery({
    queryKey: repoHomeQueryKey(repo, fixtureUrl),
    queryFn: repoHomeQueryFn(repo, fixtureUrl),
    enabled: Boolean(fixtureUrl || repo),
  })

  return { home: data ?? null, loading: isLoading, error: error?.message ?? null }
}
