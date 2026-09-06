import { useQuery } from '@tanstack/react-query'
import { flowQueryFn, flowQueryKey } from '../api/queries'

export function useFlowGraph(repo, fixtureUrl, entry, helper) {
  const { data, isLoading, error } = useQuery({
    queryKey: flowQueryKey(repo, fixtureUrl, entry, helper),
    queryFn: flowQueryFn(repo, fixtureUrl, entry, helper),
    enabled: Boolean(fixtureUrl || repo),
  })

  return { payload: data ?? null, loading: isLoading, error: error?.message ?? null }
}
