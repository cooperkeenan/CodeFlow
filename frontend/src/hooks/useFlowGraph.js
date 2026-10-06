import { useQuery } from '@tanstack/react-query'
import { flowQueryFn, flowQueryKey } from '../api/queries'

export function useFlowGraph(repo, fixtureUrl, entry, helper, route) {
  const { data, isLoading, error } = useQuery({
    queryKey: flowQueryKey(repo, fixtureUrl, entry, helper, route),
    queryFn: flowQueryFn(repo, fixtureUrl, entry, helper, route),
    enabled: Boolean(fixtureUrl || repo),
  })

  return { payload: data ?? null, loading: isLoading, error: error?.message ?? null }
}
