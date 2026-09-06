import { useQuery } from '@tanstack/react-query'
import { explainQueryFn, explainQueryKey } from '../api/queries'

export function useNodeExplanation(repo, nodeId) {
  const { data, isLoading, error } = useQuery({
    queryKey: explainQueryKey(repo, nodeId),
    queryFn: explainQueryFn(repo, nodeId),
    enabled: Boolean(repo && nodeId),
  })

  return {
    explanation: data?.explanation ?? null,
    sources: data?.sources ?? {},
    steps: data?.steps ?? {},
    loading: isLoading,
    error: error?.message ?? null,
  }
}
