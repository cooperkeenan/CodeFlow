import { useMemo } from 'react'
import { useStoreApi } from 'reactflow'

export function useMeasuredNodes(nodes) {
  const store = useStoreApi()
  return useMemo(() => {
    const internals = store.getState().nodeInternals
    return nodes.map(node => {
      const known = internals.get(node.id)
      return known?.width && known?.height
        ? { ...node, width: known.width, height: known.height }
        : node
    })
  }, [nodes, store])
}
