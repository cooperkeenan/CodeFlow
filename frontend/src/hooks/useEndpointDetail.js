import { useQuery } from '@tanstack/react-query'
import { endpointDetailQueryFn, endpointDetailQueryKey } from '../api/queries'

export function useEndpointDetail(repo, fixtureUrl, entry) {
  const { data, isLoading, error } = useQuery({
    queryKey: endpointDetailQueryKey(repo, fixtureUrl, entry),
    queryFn: endpointDetailQueryFn(repo, fixtureUrl, entry),
    enabled: Boolean(entry && (fixtureUrl || repo)),
  })

  return { detail: data ?? null, loading: isLoading, error: error?.message ?? null }
}
